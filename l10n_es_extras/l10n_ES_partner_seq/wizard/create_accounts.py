# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
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

import wizard
import netsvc
import pooler
import string

accounts_create_form = """<?xml version="1.0" encoding="utf-8"?>
<form string="Create accounts">
    <label string="Do you want to create accounts for the selected partners?" />
</form>"""

accounts_create_fields = {}

def strip0d(cadena):
    # Elimina los ceros de la derecha en una cadena de texto de dígitos
    return str(int(cadena[::-1]))[::-1]

def strip0i(cadena):
    # Elimina los ceros de la izquierda en una cadena de texto de dígitos
    return str(int(cadena))


def _createAccounts(self, cr, uid, data, context):
    partner_obj = pooler.get_pool(cr.dbname).get('res.partner')
    account_obj = pooler.get_pool(cr.dbname).get('account.account')
    sequence_obj = pooler.get_pool(cr.dbname).get('ir.sequence')

    account_type_obj = pooler.get_pool(cr.dbname).get('account.account.type')
    ids = account_type_obj.search(cr, uid, [('code', '=', 'terceros - rec')]) # Busca tipo cuenta de usuario rec
    acc_user_type_rec = ids and ids[0]
    ids = account_type_obj.search(cr, uid, [('code', '=', 'terceros - pay')]) # Busca tipo cuenta de usuario pay
    acc_user_type_pay = ids and ids[0]
    if not acc_user_type_rec and not acc_user_type_pay:
        return

    def link_account(ref, parent_code, acc_type, acc_user_type, acc_property):
        """
        parent_code: Código del padre (Ej.: 4300)
        type: Puede ser 'payable' o 'receivable'
        acc_property: 'property_account_receivable' o 'property_account_payable'"""
        acc_code = parent_code + ref  # acc_code es el nuevo código de subcuenta
        args = [('code', '=', acc_code)]
        if not account_obj.search(cr, uid, args):
            vals = {
            'name': partner.name,
            'code': acc_code,
            'type': acc_type,
            'user_type': acc_user_type,
            'shortcut': strip0d(acc_code[:4]) + "." + strip0i(acc_code[-5:]),
            }
            args = [('code', '=', parent_code)]
            parent_acc_ids = account_obj.search(cr, uid, args) # Busca id de la subcuenta padre
            if parent_acc_ids:
                vals['parent_id'] = parent_acc_ids[0]
            acc_id = account_obj.create(cr, uid, vals)
            vals = {acc_property: acc_id}
            partner_obj.write(cr, uid, [partner.id], vals) # Asocia la nueva subcuenta con el partner

    for partner in partner_obj.browse(cr, uid, data['ids'], context=context):
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
                link_account(ref, '430', 'receivable', acc_user_type_rec, 'property_account_receivable')

            if partner.supplier:
                link_account(ref, '400', 'payable', acc_user_type_pay, 'property_account_payable')
    return {}


class create_accounts(wizard.interface):
    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : accounts_create_form,
                    'fields' : accounts_create_fields,
                    'state' : [('end', 'Cancel'),('create', 'Create accounts') ]}
        },
        'create' : {
            'actions' : [],
            'result' : {'type' : 'action',
                    'action' : _createAccounts,
                    'state' : 'end'}
        },
    }
create_accounts("l10n_ES_partner_seq.create_accounts")
