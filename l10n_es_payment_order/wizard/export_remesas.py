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
# Añadidos conceptos extras del CSB 19: Acysos S.L. 2011
#   Ignacio Ibeas <ignacio@acysos.com>
#
# Migración de wizard.interface para la 6.1: Pexego Sistemas Informáticos. 2012
#   Marta Vázquez Rodríguez <marta@pexego.es>
#
# Refactorización. Acysos S.L. (http://www.acysos.com) 2012
#   Ignacio Ibeas <ignacio@acysos.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields
import base64
from tools.translate import _
from log import *



class wizard_payment_file_spain(osv.osv_memory):
    _name = 'wizard.payment.file.spain'
    _columns = {
        'join': fields.boolean('Join payment lines of the same partner and bank account'),
        'pay': fields.binary('Payment order file', readonly=True),
        'pay_fname': fields.char('File name', size=64),
        'note': fields.text('Log')
    }

    def create_payment_file(self, cr, uid, ids, context):
        converter = self.pool.get('payment.converter.spain')
        txt_remesa = ''

        form_obj = self.browse(cr, uid, ids)[0]
        try:
            orden = self.pool.get('payment.order').browse(cr, uid, context['active_id'], context)
            if not orden.line_ids:
                raise Log( _('User error:\n\nWizard can not generate export file, there are not payment lines.'), True )
            if orden.create_account_moves == 'direct-payment' and (orden.state != 'open' and orden.state != 'done'):
                raise Log( _('User error:\n\nIf direct payment is selected to create the account moves, you should confirm payments befores. Creating the files will make the payments.'), True )


            # Comprobamos que exista número de C.C. y que tenga 20 dígitos
            if not orden.mode.bank_id:
                raise Log( _('User error:\n\nThe bank account of the company %s is not defined.') % (orden.mode.partner_id.name), True )
            cc = converter.digits_only(cr,uid,orden.mode.bank_id.acc_number)
            if len(cc) != 20:
                raise Log( _('User error:\n\nThe bank account number of the company %s has not 20 digits.') % (orden.mode.partner_id.name), True)

            # Comprobamos que exista el CIF de la compañía asociada al C.C. del modo de pago
            if not orden.mode.bank_id.partner_id.vat:
                raise Log(_('User error:\n\nThe company VAT number related to the bank account of the payment mode is not defined.'), True)

            recibos = []
            if form_obj.join:
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
                        'name': partner.ref or str(l.partner_id.id),
                        'amount': reduce(lambda x, y: x+y, [l.amount for l in lineas], 0),
                        'communication': reduce(lambda x, y: x+' '+(y or ''), [l.name+' '+l.communication for l in lineas], ''),
                        'communication2': reduce(lambda x, y: x+' '+(y or ''), [l.communication2 for l in lineas], ''),
                        'date': max([l.date for l in lineas]),
                        'ml_maturity_date': max([l.ml_maturity_date for l in lineas]),
                        'create_date': max([l.create_date for l in lineas]),
                        'ml_date_created': max([l.ml_date_created for l in lineas]),
                        'ml_inv_ref': [l.ml_inv_ref for l in lineas]
                    })
            else:
                # Cada línea de pago es un recibo
                for l in orden.line_ids:
                    recibos.append({
                        'partner_id': l.partner_id,
                        'bank_id': l.bank_id,
                        'name': l.partner_id.ref or str(l.partner_id.id),
                        'amount': l.amount,
                        'communication': l.name+' '+l.communication,
                        'communication2': l.communication2,
                        'date': l.date,
                        'ml_maturity_date': l.ml_maturity_date,
                        'create_date': l.create_date,
                        'ml_date_created': l.ml_date_created,
                        'ml_inv_ref':[l.ml_inv_ref]
                    })

            if orden.mode.require_bank_account:
                for line in recibos:
                    ccc = line['bank_id'] and line['bank_id'].acc_number or False
                    if not ccc:
                        raise Log(_('User error:\n\nThe bank account number of the customer %s is not defined and current payment mode enforces all lines to have a bank account.') % (line['partner_id'].name), True)
                    ccc = converter.digits_only(cr,uid,ccc)
                    if len(ccc) != 20:
                        raise Log(_('User error:\n\nThe bank account number of the customer %s has not 20 digits.') % (line['partner_id'].name), True)

            if orden.mode.tipo == 'csb_19':
                csb = self.pool.get('csb.19')
            elif orden.mode.tipo == 'csb_32':
                csb = self.pool.get('csb.32')
            elif orden.mode.tipo == 'csb_34':
                csb = self.pool.get('csb.34')
            elif orden.mode.tipo == '34_01':
                csb = self.pool.get('csb.3401')
            elif orden.mode.tipo == 'csb_58':
                csb = self.pool.get('csb.58')
            else:
                raise Log(_('User error:\n\nThe payment mode is not CSB 19, CSB 32, CSB 34 or CSB 58'), True)
            txt_remesa = csb.create_file(cr, uid, orden, recibos, context)

        except Log, log:
            form_obj.write({'note': log(),'pay': False})
            return True

        else:
            # Ensure line breaks use MS-DOS (CRLF) format as standards require.
            txt_remesa = txt_remesa.replace('\r\n','\n').replace('\n','\r\n')

            file_remesa = base64.encodestring(txt_remesa.encode('utf-8'))
            fname = (_('Remittance_%s_%s.txt') %(orden.mode.tipo, orden.reference)).replace('/','-')
            # Borrar posible anterior adjunto de la exportación
            obj_attachment = self.pool.get('ir.attachment')
            attachment_ids = obj_attachment.search(cr, uid, [('name', '=', fname), ('res_model', '=', 'payment.order')])
            if len(attachment_ids):
                obj_attachment.unlink(cr, uid, attachment_ids)
            # Adjuntar nuevo archivo de remesa
            obj_attachment.create(cr, uid, {
                'name': fname,
                'datas': file_remesa,
                'datas_fname': fname,
                'res_model': 'payment.order',
                'res_id': orden.id,
                }, context=context)
            log = _("Successfully Exported\n\nSummary:\n Total amount paid: %.2f\n Total Number of Payments: %d\n") % (orden.total, len(recibos))

            form_obj.write({'note': log,'pay': file_remesa,'pay_fname': fname})

            return True
wizard_payment_file_spain()
