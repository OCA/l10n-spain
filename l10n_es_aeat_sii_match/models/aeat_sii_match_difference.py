# Copyright 2018 Studio73 - Abraham Anes
# Copyright 2019 Studio73 - Pablo Fuentes
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SiiMatchDifferences(models.Model):
    _name = "l10n.es.aeat.sii.match.difference"
    _description = "SII match difference"

    invoice_id = fields.Many2one(string="Related invoice", comodel_name="account.move")
    report_id = fields.Many2one(
        string="Related SII match report", comodel_name="l10n.es.aeat.sii.match.result"
    )
    sii_field = fields.Char(string="SII field name", copy=False)
    sii_return_field_value = fields.Char(string="SII return field value", copy=False)
    sii_sent_field_value = fields.Char(string="SII sent field value", copy=False)
