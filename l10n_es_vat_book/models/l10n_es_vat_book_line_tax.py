# -*- coding: utf-8 -*-
# Copyright 2017 Praxya (http://praxya.com/)
#                Daniel Rodriguez Lijo <drl.9319@gmail.com>
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
#                <contact@eficent.com>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import api, fields, models


class L10nEsVatBookLineTax(models.Model):
    _name = 'l10n.es.vat.book.line.tax'

    vat_book_line_id = fields.Many2one(comodel_name='l10n.es.vat.book.line',
                                       required=True, ondelete='cascade')

    base_amount = fields.Float(
        string='Base')

    tax_id = fields.Many2one(comodel_name='account.tax', string='Tax')

    tax_rate = fields.Float(string='Tax Rate (%)', compute='_compute_tax_rate')

    tax_amount = fields.Float(
        string='Tax fee')

    total_amount = fields.Float(
        string='Total')

    move_line_ids = fields.Many2many(
        comodel_name='account.move.line', string='Move Lines')

    @api.multi
    @api.depends('tax_id')
    def _compute_tax_rate(self):
        for rec in self:
            rec.tax_rate = rec.tax_id.amount
