# -*- coding: utf-8 -*-
# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# Copyright 2017 - Eficent Business and IT Consulting Services, S.L.
#                  <contact@eficent.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    eu_triangular_deal = fields.Boolean(
        string='EU Triangular deal',
        help='This invoice constitutes a triangular operation for the '
             'purposes of intra-community operations.',
        readonly=True, states={'draft': [('readonly', False)]})

    @api.model
    def line_get_convert(self, line, part):
        """Copy from invoice to move lines"""
        res = super(AccountInvoice, self).line_get_convert(line, part)
        res['aeat_349_operation_key'] = line.get(
            'aeat_349_operation_key', False)
        return res

    @api.model
    def invoice_line_move_line_get(self):
        """We pass on the operation key from invoice line to the move line"""
        ml_dicts = super(AccountInvoice, self).invoice_line_move_line_get()
        for ml_dict in ml_dicts:
            invl_id = ml_dict['invl_id']
            invl = self.env['account.invoice.line'].browse(invl_id)
            ml_dict['aeat_349_operation_key'] = invl.aeat_349_operation_key.id
        return ml_dicts
