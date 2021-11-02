# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields


class TicketBAITaxMap(models.Model):
    _name = 'tbai.tax.map'
    _description = 'TicketBAI Tax Map'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name', required=True)
    tax_template_ids = fields.Many2many(
        comodel_name='account.tax.template', string="Taxes")
