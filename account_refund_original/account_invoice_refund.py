# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#        Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp.osv import orm


class AccountInvoiceRefund(orm.TransientModel):
    """Refunds invoice"""
    _inherit = "account.invoice.refund"

    def compute_refund(self, cr, uid, ids, mode='refund', context=None):
        """
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: the account invoice refund’s ID or list of IDs
        """
        inv_obj = self.pool['account.invoice']
        if context is None:
            context = {}
        result = super(AccountInvoiceRefund, self).compute_refund(
            cr, uid, ids, mode, context)

        # An example of result['domain'] computed by the parent wizard is:
        # [('type', '=', 'out_refund'), ('id', 'in', [43L, 44L])]
        # The created refund invoice is the first invoice in the
        # ('id', 'in', ...) tupla
        created_inv = [x[2] for x in result['domain']
                       if x[0] == 'id' and x[1] == 'in']
        if context.get('active_ids') and created_inv and created_inv[0]:
            for form in self.read(cr, uid, ids, context=context):
                refund_inv_id = created_inv[0][0]
                inv_obj.write(cr, uid, [refund_inv_id], {
                    'origin_invoices_ids': [(6, 0, context.get('active_ids'))],
                    'refund_invoices_description': form['description'] or ''
                })
        return result
