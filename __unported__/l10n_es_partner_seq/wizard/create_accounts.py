# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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

from openerp.osv import orm, fields
from openerp.tools.translate import _
import string

def strip0d(cadena):
    # Elimina los ceros de la derecha en una cadena de texto de dígitos
    return str(int(cadena[::-1]))[::-1]

def strip0i(cadena):
    # Elimina los ceros de la izquierda en una cadena de texto de dígitos
    return str(int(cadena))

class create_accounts(orm.TransientModel):
    """Wizard to create accounts for partners"""
    _name = "account.create.accounts"
    _description = "create accounts wizard"

    _columns = {
        'parent_receivable': fields.many2one(
            'account.account',
            'Parent Receivable Account',
            required=True,
            domain=[('type','=','view')],
            help='Parent for the receivable account, like 4300 for clients, 4400 for debtors, ... It also will be used as the code prefix of the created account.\nTip: Save the most used parent account as the default value.'),
        'parent_payable': fields.many2one(
            'account.account',
            'Parent Payable Account',
            required=True,
            domain=[('type','=','view')],
            help='Parent for the payable account, like 4000 for suppliers, 4100 for creditors, ... It also will be used as the code prefix of the created account.\nTip: Save the most used parent account as the default value.'),
        'num_digits': fields.integer(
            'Number of digits',
            required=True,
            help='Number of digits of the account codes.'),
    }

    def _get_num_digits(self, cr, uid, data, context=None):
        """ To know the number of digits of the company accounts, we look for
            the default receivable account of the company that the user belongs to"""
        if context is None:
            context = {}
        users_obj = self.pool.get('res.users')
        property_obj = self.pool.get('ir.property')
        account_obj = self.pool.get('account.account')
        user = users_obj.browse(cr, uid, uid, context)
        property_ids = property_obj.search(cr, uid, [('name','=','property_account_receivable' ), ('company_id','=',user.company_id.id), ('res_id','=',False), ('value_reference','!=',False)])
        num_digits = False
        if property_ids:
            prop = property_obj.browse(cr, uid, property_ids[0], context)
            if prop.value_reference:
                code = account_obj.read(cr, uid, int(prop.value_reference.split(',')[1]), ['code'], context)['code']
                num_digits = len(code)
        return num_digits

    _defaults = {
        'num_digits': _get_num_digits,
    }

    def create_accounts(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        partner_obj = self.pool.get('res.partner')
        account_obj = self.pool.get('account.account')
        sequence_obj = self.pool.get('ir.sequence')

        account_type_obj = self.pool.get('account.account.type')
        res_ids = account_type_obj.search(cr, uid, [('code', '=', 'receivable')]) # Busca tipo cuenta de usuario rec
        acc_user_type_rec = res_ids and res_ids[0]
        res_ids = account_type_obj.search(cr, uid, [('code', '=', 'payable')]) # Busca tipo cuenta de usuario pay
        acc_user_type_pay = res_ids and res_ids[0]
        if not acc_user_type_rec or not acc_user_type_pay:
            raise osv.except_osv(_('Error !'), _("Account types with codes 'terceros - rec' and 'terceros - pay' have not been defined!"))

        def link_account(ref, parent_account, acc_type, acc_user_type, acc_property):
            """
            parent_account: Parent account (For ex.: 4300 Customers)
            type: It can be 'payable' or 'receivable'
            acc_property: 'property_account_receivable' or 'property_account_payable'"""
            acc_code = parent_account.code + ref  # acc_code es el nuevo código de subcuenta
            if not account_obj.search(cr, uid, [('code', '=', acc_code)]):
                vals = {
                    'name': partner.name,
                    'code': acc_code,
                    'type': acc_type,
                    'user_type': acc_user_type,
                    'shortcut': strip0d(acc_code[:4]) + "." + strip0i(acc_code[-5:]),
                    'reconcile': True,
                    'parent_id': parent_account.id,
                }
                acc_id = account_obj.create(cr, uid, vals)
                vals = {acc_property: acc_id}
                partner_obj.write(cr, uid, [partner.id], vals) # Asocia la nueva subcuenta con el partner

        form = self.browse(cr, uid, ids[0], context=context)
        for partner in partner_obj.browse(cr, uid, context['active_ids'], context=context):
            if not partner.customer and not partner.supplier:
                continue
            if not partner.ref or not partner.ref.strip():
                ref = sequence_obj.get(cr, uid, 'res.partner')
                vals = {'ref': ref}
                partner_obj.write(cr, uid, [partner.id], vals)
            else:
                 ref = partner.ref

            ref = ''.join([i for i in ref if i in string.digits]) # Solo nos interesa los dígitos del código
            if (ref.isdigit()):
                if partner.customer:
                    len_ref = form.num_digits - len(form.parent_receivable.code) # longitud del código que aprovechamos
                    if len_ref > 0:
                        link_account(ref[-len_ref:].zfill(len_ref), form.parent_receivable, 'receivable', acc_user_type_rec, 'property_account_receivable')

                if partner.supplier:
                    len_ref = form.num_digits - len(form.parent_payable.code) # longitud del código que aprovechamos
                    if len_ref > 0:
                        link_account(ref[-len_ref:].zfill(len_ref), form.parent_payable, 'payable', acc_user_type_pay, 'property_account_payable')
        return { 'type': 'ir.actions.act_window_close' }


create_accounts()
