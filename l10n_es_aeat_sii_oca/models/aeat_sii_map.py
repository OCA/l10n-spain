# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models
from odoo.fields import Domain


class AeatSiiMap(models.Model):
    _name = "aeat.sii.map"
    _description = "Aeat SII Map"

    @api.constrains("date_from", "date_to")
    def _unique_date_range(self):
        for record in self:
            record._unique_date_range_one()

    def _unique_date_range_one(self):
        # Based in l10n_es_aeat module
        domain = Domain("id", "!=", self.id)
        if self.date_from and self.date_to:
            domain &= (
                (
                    Domain("date_from", "<=", self.date_to)
                    & Domain("date_from", ">=", self.date_from)
                )
                | (
                    Domain("date_to", "<=", self.date_to)
                    & Domain("date_to", ">=", self.date_from)
                )
                | (
                    Domain("date_from", "=", False)
                    & Domain("date_to", ">=", self.date_from)
                )
                | (
                    Domain("date_to", "=", False)
                    & Domain("date_from", "<=", self.date_to)
                )
            )
        elif self.date_from:
            domain &= Domain("date_to", ">=", self.date_from)
        elif self.date_to:
            domain &= Domain("date_from", "<=", self.date_to)
        date_lst = self.search(domain)
        if date_lst:
            raise exceptions.UserError(
                self.env._(
                    "Error! The dates of the record overlap with an existing record."
                )
            )

    name = fields.Char(string="Model", required=True)
    date_from = fields.Date()
    date_to = fields.Date()
    map_lines = fields.One2many(
        comodel_name="aeat.sii.map.lines", inverse_name="sii_map_id", string="Lines"
    )
    tax_agency_id = fields.Many2one(comodel_name="aeat.tax.agency", string="Tax Agency")


class AeatSiiMapLines(models.Model):
    _name = "aeat.sii.map.lines"
    _description = "Aeat SII Map Lines"

    code = fields.Char(required=True)
    name = fields.Char()
    tax_xmlid_ids = fields.Many2many(
        comodel_name="l10n.es.aeat.map.tax.line.tax", string="Taxes templates"
    )
    sii_map_id = fields.Many2one(
        comodel_name="aeat.sii.map", string="Aeat SII Map", ondelete="cascade"
    )
