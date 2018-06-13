# -*- coding: utf-8 -*-
# Copyright 2018 Abraham Anes <abraham@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SiiMatchDifferences(models.Model):
    _name = 'l10n.es.aeat.sii.match.differences'

    invoice_id = fields.Many2one(
        string="Related invoice", comodel_name='account.invoice'
    )
    report_id = fields.Many2one(
        string="Related SII match report",
        comodel_name='l10n.es.aeat.sii.match.result'
    )
    sii_field = fields.Char(
        string="SII field name", copy=False,
    )
    sii_return_field_value = fields.Char(
        string="SII return field value", copy=False,
    )
    sii_sent_field_value = fields.Char(
        string="SII sent field value", copy=False,
    )
