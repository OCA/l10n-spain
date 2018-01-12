# -*- coding: utf-8 -*-
# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# Copyright 2017 - Eficent Business and IT Consulting Services, S.L.
#                  <contact@eficent.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountInvoiceLine(models.Model):
    """Inheritance of account invoice line to add some fields:
    - AEAT_349_operation_key
    """
    _inherit = 'account.invoice.line'

    aeat_349_operation_key = fields.Many2one(
        string='AEAT 349 Operation key',
        comodel_name='aeat.349.map.line',
        compute='_compute_aeat_349_operation_key'
    )

    @api.depends('invoice_line_tax_ids', 'invoice_id.eu_triangular_deal')
    def _compute_aeat_349_operation_key(self):
        for rec in self:
            if rec.invoice_line_tax_ids:
                taxes = rec.mapped('invoice_line_tax_ids').filtered(
                    lambda x: x.aeat_349_operation_key)
                if taxes:
                    if rec.invoice_id.eu_triangular_deal:
                        rec.aeat_349_operation_key = self.env.ref(
                            'l10n_es_aeat_mod349.aeat_349_map_line_T')
                    else:
                        rec.aeat_349_operation_key = \
                            taxes[0].aeat_349_operation_key
            else:
                rec.aeat_349_operation_key = self.env['aeat.349.map.line']
