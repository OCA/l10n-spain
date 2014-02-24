# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
# Copyright (c) 2006 ACYSOS S.L.. (http://acysos.com) All Rights Reserved.
#    Pedro Tarrafeta <pedro@acysos.com>
#
# Corregido para instalación TinyERP estándar 4.2.0: Zikzakmedia S.L. 2008
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Añadidas cuentas de remesas y tipos de pago. 2008
#    Pablo Rocandio <salbet@gmail.com>
#
# Corregido para instalación OpenERP 5.0.0 sobre account_payment_extension: Zikzakmedia S.L. 2009
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Adaptación para instalación OpenERP 6.0.0 sobre account_payment_extension: Zikzakmedia S.L. 2010
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Añadidos conceptos extras del CSB 19: Acysos S.L. 2011
#   Ignacio Ibeas <ignacio@acysos.com>
#
#    $Id$
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
from openerp import pooler
from openerp.tools.translate import _



class payment_mode(osv.osv):
    _name= 'payment.mode'
    _inherit = 'payment.mode'

    def onchange_partner(self, cr, uid, ids, partner_id):
        if partner_id:
            pool = pooler.get_pool(cr.dbname)
            obj = pool.get('res.partner')
            field = ['name']
            ids = [partner_id]
            filas = obj.read(cr, uid, ids, field) 
            return {'value':{'nombre': filas[0]["name"][:40]}}
        return {'value':{'nombre': ""}}

    _columns = {
        'tipo': fields.selection([('none','None'),('csb_19','CSB 19'),('csb_32','CSB 32'),('csb_34','CSB 34'),('34_01','CSB 34-01'),('csb_58','CSB 58')], 'Type of payment file', size=6, select=True, required=True),
        'sufijo': fields.char('suffix',size=3, select=True),
        'partner_id': fields.many2one('res.partner', 'Partner', select=True),
        'nombre': fields.char('Company name in file', size=40),
        'cif': fields.related('partner_id','vat', type='char', string='VAT code', select=True),
        # Código INE (9 dígitos)
        'ine': fields.char('INE code',size=9),
        'cedente': fields.char('Cedente', size=15),
        # Incluir registro obligatorio de domicilio (para no domiciliados)
        'inc_domicile': fields.boolean('Include domicile', help='Add partner domicile records to the exported file (CSB 58)'),
        # Usar formato alternativo para el registro de domicilio
        'alt_domicile_format': fields.boolean('Alt. domicile format', help='Alternative domicile record format'),
        # Require bank account?
        'require_bank_account': fields.boolean('Require bank account', help='If your bank allows you to send orders without the bank account info, you may disable this option'),
        'csb34_type': fields.selection([('transfer', 'Transfer'),('promissory_note', 'Promissory Note'),('cheques', 'Cheques'),('certified_payments', 'Certified Payments')], 'Type of CSB 34 payment'),
        'text1': fields.char('Line 1', size=36, help='Enter text and/or select a field of the invoice to include as a description in the letter. The possible values ​​are: ${amount}, ${communication}, {communication2}, {date}, {ml_maturity_date}, {create_date}, {ml_date_created}'),
        'text2': fields.char('Line 2', size=36, help='Enter text and/or select a field of the invoice to include as a description in the letter. The possible values ​​are: ${amount}, ${communication}, {communication2}, {date}, {ml_maturity_date}, {create_date}, {ml_date_created}'),
        'text3': fields.char('Line 3', size=36, help='Enter text and/or select a field of the invoice to include as a description in the letter. The possible values ​​are: ${amount}, ${communication}, {communication2}, {date}, {ml_maturity_date}, {create_date}, {ml_date_created}'),
        'payroll_check': fields.boolean('Payroll Check', help='Check it if you want to add the 018 data type in the file (the vat of the recipient is added in the 018 data type).'),
        'add_date': fields.boolean('Add Date', help='Check it if you want to add the 910 data type in the file to include the payment date.'),
        'send_type':fields.selection([
            ('mail','Ordinary Mail'),
            ('certified_mail','Certified Mail'),
            ('other','Other'),
        ],'Send Type', help="The sending type of the payment file"),
        'not_to_the_order':fields.boolean('Not to the Order'),
        'barred':fields.boolean('Barred'),
        'cost_key':fields.selection([
            ('payer','Expense of the Payer'),
            ('recipient','Expense of the Recipient'),
        ],'Cost Key'),
        'concept':fields.selection([
            ('payroll','Payroll'),
            ('pension','Pension'),
            ('other','Other'),
        ],'Concept of the Order', help="Concept of the Order."),
        'direct_pay_order':fields.boolean('Direct Pay Order', help="By default 'Not'."),
        'csb19_extra_concepts': fields.boolean('Extra Concepts', help='Check it if you want to add the invoice lines to the extra concepts (Max. 15 lines)'),
    }

    _defaults = {
        'tipo': lambda *a: 'none',
        'sufijo': lambda *a: '000',
        'inc_domicile': lambda *a: False,
        'alt_domicile_format': lambda *a: False,

        # Override default: We want to be safe so we require bank account by default
        'require_bank_account': lambda *a: True, 
        'csb34_type': lambda *a: 'transfer',
        'text1': lambda self,cr,uid,context: _('Dear Sir'),
        'text2': lambda self,cr,uid,context: _('Payment ref.')+' ${communication}',
        'text3': lambda self,cr,uid,context: _('Total:')+' ${amount}',
        'send_type': lambda *a: 'mail',
        'not_to_the_order': lambda *a: True,
        'barred': lambda *a: True,
        'cost_key': lambda *a: 'payer',
        'concept': lambda *a: 'other',
        'direct_pay_order': lambda *a: False,
    }

payment_mode()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
