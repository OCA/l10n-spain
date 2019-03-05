# -*- coding: utf-8 -*-
from odoo import models, api, fields, _


class L10nEsVatBookMap(models.Model):
    _name = 'l10n.es.vat.book.map'

    tax_id = fields.Many2one(comodel_name="account.tax", string="Tax")
    tax_ids = fields.Many2many(
        comodel_name="account.tax",
        string="Deductible Taxes",
    )
