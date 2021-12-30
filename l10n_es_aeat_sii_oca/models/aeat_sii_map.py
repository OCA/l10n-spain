# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models


class AeatSiiMap(models.Model):
    _name = "aeat.sii.map"
    _description = "Aeat SII Map"

    @api.constrains("date_from", "date_to")
    def _unique_date_range(self):
        for record in self:
            record._unique_date_range_one()

    def _unique_date_range_one(self):
        # Based in l10n_es_aeat module
        domain = [("id", "!=", self.id)]
        if self.date_from and self.date_to:
            domain += [
                "|",
                "&",
                ("date_from", "<=", self.date_to),
                ("date_from", ">=", self.date_from),
                "|",
                "&",
                ("date_to", "<=", self.date_to),
                ("date_to", ">=", self.date_from),
                "|",
                "&",
                ("date_from", "=", False),
                ("date_to", ">=", self.date_from),
                "|",
                "&",
                ("date_to", "=", False),
                ("date_from", "<=", self.date_to),
            ]
        elif self.date_from:
            domain += [("date_to", ">=", self.date_from)]
        elif self.date_to:
            domain += [("date_from", "<=", self.date_to)]
        date_lst = self.search(domain)
        if date_lst:
            raise exceptions.UserError(
                _("Error! The dates of the record overlap with an existing " "record.")
            )

    name = fields.Char(string="Model", required=True)
    date_from = fields.Date()
    date_to = fields.Date()
    map_lines = fields.One2many(
        comodel_name="aeat.sii.map.lines", inverse_name="sii_map_id", string="Lines"
    )


class AeatSiiMapLines(models.Model):
    _name = "aeat.sii.map.lines"
    _description = "Aeat SII Map Lines"

    code = fields.Char(required=True)
    name = fields.Char()
    taxes = fields.Many2many(comodel_name="account.tax.template")
    sii_map_id = fields.Many2one(
        comodel_name="aeat.sii.map", string="Aeat SII Map", ondelete="cascade"
    )
