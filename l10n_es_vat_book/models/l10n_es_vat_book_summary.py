# -*- coding: utf-8 -*-
# Copyright 2017 Praxya (http://praxya.com/)
#                Daniel Rodriguez Lijo <drl.9319@gmail.com>
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
#                <contact@eficent.com>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import fields, models


class L10nEsVatBookIssuedSummary(models.Model):
    _name = 'l10n.es.vat.book.summary'

    vat_book_id = fields.Many2one(
        comodel_name='l10n.es.vat.book',
        string='Vat Book id')

    book_type = fields.Selection(selection=[
        ('issued', 'Issued'),
        ('received', 'Received'),
    ], string='Book type')

    base_amount = fields.Float(
        string='Base amount',
        readonly="True")

    tax_amount = fields.Float(
        string='Tax amount',
        readonly="True")

    total_amount = fields.Float(
        string='Total amount',
        readonly="True")
