# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2006 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#                       Pedro Tarrafeta <pedro@acysos.com>
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
#
# Corregido para instalación TinyERP estándar 4.2.0: Zikzakmedia S.L. 2008
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Añadidas cuentas de remesas y tipos de pago. 2008
#    Pablo Rocandio <salbet@gmail.com>
#
# Rehecho de nuevo para instalación OpenERP 5.0.0 sobre account_payment_extension: Zikzakmedia S.L. 2009
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import pooler
import wizard
import base64
from tools.translate import _
from converter import *
import csb_19
import csb_32
import csb_34
import csb_58

join_form = """<?xml version="1.0"?>
<form string="Payment order export">
    <field name="join"/>
</form>"""

join_fields = {
    'join' : {'string':'Join payment lines of the same partner and bank account', 'type':'boolean'},
}

export_form = """<?xml version="1.0"?>
<form string="Payment order export">
    <field name="pay" filename="pay_fname"/>
    <field name="pay_fname" invisible="1"/>
    <field name="note" colspan="4" nolabel="1"/>
</form>"""

export_fields = {
    'pay' : {
        'string':'Payment order file',
        'type':'binary',
        'required': False,
        'readonly':True,
    },
    'pay_fname': {'string':'File name', 'type':'char', 'size':64},
    'note' : {'string':'Log', 'type':'text'},
}


def _create_payment_file(self, cr, uid, data, context):

    txt_remesa = ''
    num_lineas_opc = 0

    try:
        pool = pooler.get_pool(cr.dbname)
        orden = pool.get('payment.order').browse(cr, uid, data['id'], context)
        if not orden.line_ids:
            raise Log( _('User error:\n\nWizard can not generate export file, there are not payment lines.'), True )

        # Comprobamos que exista número de C.C. y que tenga 20 dígitos
        if not orden.mode.bank_id:
            raise Log( _('User error:\n\nThe bank account of the company %s is not defined.') % (orden.mode.partner_id.name), True )
        cc = digits_only(orden.mode.bank_id.acc_number)
        if len(cc) != 20:
            raise Log( _('User error:\n\nThe bank account number of the company %s has not 20 digits.') % (orden.mode.partner_id.name), True)

        # Comprobamos que exista el CIF de la compañía asociada al C.C. del modo de pago
        if not orden.mode.bank_id.partner_id.vat:
            raise Log(_('User error:\n\nThe company VAT number related to the bank account of the payment mode is not defined.'), True)

        recibos = []
        if data['form']['join']:
            # Lista con todos los partners+bancos diferentes de la remesa
            partner_bank_l = reduce(lambda l, x: x not in l and l.append(x) or l,
                                     [(recibo.partner_id,recibo.bank_id) for recibo in orden.line_ids], [])
            # Cómputo de la lista de recibos agrupados por mismo partner+banco.
            # Los importes se suman, los textos se concatenan con un espacio en blanco y las fechas se escoge el máximo
            for partner,bank in partner_bank_l:
                lineas = [recibo for recibo in orden.line_ids if recibo.partner_id==partner and recibo.bank_id==bank]
                recibos.append({
                    'partner_id': partner,
                    'bank_id': bank,
                    'name': partner.ref,
                    'amount': reduce(lambda x, y: x+y, [l.amount for l in lineas], 0),
                    'communication': reduce(lambda x, y: x+' '+(y or ''), [l.name+' '+l.communication for l in lineas], ''),
                    'communication2': reduce(lambda x, y: x+' '+(y or ''), [l.communication2 for l in lineas], ''),
                    'date': max([l.date for l in lineas]),
                    'ml_maturity_date': max([l.ml_maturity_date]),
                    'create_date': max([l.create_date]),
                    'ml_date_created': max([l.ml_date_created]),
                })
        else:
            # Cada línea de pago es un recibo
            for l in orden.line_ids:
                recibos.append({
                    'partner_id': l.partner_id,
                    'bank_id': l.bank_id,
                    'name': l.partner_id.ref,
                    'amount': l.amount,
                    'communication': l.name+' '+l.communication,
                    'communication2': l.communication2,
                    'date': l.date,
                    'ml_maturity_date': l.ml_maturity_date,
                    'create_date': l.create_date,
                    'ml_date_created': l.ml_date_created,
                })

        if orden.mode.require_bank_account:
            for line in recibos:
                ccc = line['bank_id'] and line['bank_id'].acc_number or False
                if not ccc:
                    raise Log(_('User error:\n\nThe bank account number of the customer %s is not defined and current payment mode enforces all lines to have a bank account.') % (line['partner_id'].name), True)
                ccc = digits_only(ccc)
                if len(ccc) != 20:
                    raise Log(_('User error:\n\nThe bank account number of the customer %s has not 20 digits.') % (line['partner_id'].name), True)

        if orden.mode.tipo == 'csb_19':
            csb = csb_19.csb_19()
        elif orden.mode.tipo == 'csb_32':
            csb = csb_32.csb_32()
        elif orden.mode.tipo == 'csb_34':
            csb = csb_34.csb_34()
        elif orden.mode.tipo == 'csb_58':
            csb = csb_58.csb_58()
        else:
            raise Log(_('User error:\n\nThe payment mode is not CSB 19, CSB 32, CSB 34 or CSB 58'), True)
        txt_remesa = csb.create_file(pool, cr, uid, orden, recibos, context)

    except Log, log:
        return {
            'note': log(), 
            'reference': orden.id, 
            'pay': False, 
            'state':'failed'
        }
    else:
        # Ensure line breaks use MS-DOS (CRLF) format as standards require.
        txt_remesa = txt_remesa.replace('\r\n','\n').replace('\n','\r\n')

        file = base64.encodestring(txt_remesa)
        fname = (_('remesa') + '_' + orden.mode.tipo + '_' + orden.reference + '.txt').replace('/','-')
        pool.get('ir.attachment').create(cr, uid, {
            'name': _('Remesa ') + orden.mode.tipo + ' ' + orden.reference,
            'datas': file,
            'datas_fname': fname,
            'res_model': 'payment.order',
            'res_id': orden.id,
            }, context=context)
        log = _("Successfully Exported\n\nSummary:\n Total amount paid: %.2f\n Total Number of Payments: %d\n") % (-orden.total, len(recibos))
        pool.get('payment.order').set_done(cr,uid,orden.id,context)
        return {
            'note': log, 
            'reference': orden.id, 
            'pay': file, 
            'pay_fname': fname, 
            'state': 'succeeded',
        }


class wizard_payment_file_spain(wizard.interface):
    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                        'arch' : join_form,
                        'fields' : join_fields,
                        'state' : [('export', 'Ok','gtk-ok') ]}
        },
        'export': {
            'actions' : [_create_payment_file],
            'result' : {'type' : 'form',
                        'arch' : export_form,
                        'fields' : export_fields,
                        'state' : [('end', 'Ok','gtk-ok') ]}
        }

    }
wizard_payment_file_spain('export_payment_file_spain')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

