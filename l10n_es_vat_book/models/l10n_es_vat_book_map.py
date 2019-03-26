# -*- coding: utf-8 -*-
from odoo import models, api, fields, _


class L10nEsVatBookMap(models.Model):
    _name = 'l10n.es.vat.book.map'

    tax_id = fields.Many2one(
        string="Tax",
        comodel_name="account.tax.template",
    )
    tax_ids = fields.Many2many(
        string="Deductible Taxes",
        comodel_name="account.tax.template",
    )
