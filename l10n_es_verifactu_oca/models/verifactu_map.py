# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models


class AeatVerifactuMap(models.Model):
    _name = "verifactu.map"
    _description = "VERI*FACTU mapping"

    name = fields.Char(string="Model", required=True)
    date_from = fields.Date()
    date_to = fields.Date()
    map_lines = fields.One2many(
        comodel_name="verifactu.map.line",
        inverse_name="verifactu_map_id",
        string="Lines",
    )

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


class AeatVerifactuMapLines(models.Model):
    _name = "verifactu.map.line"
    _description = "VERI*FACTU mapping line"

    code = fields.Char(required=True)
    name = fields.Char()
    tax_xmlid_ids = fields.Many2many(
        comodel_name="l10n.es.aeat.map.tax.line.tax", string="Taxes templates"
    )
    verifactu_map_id = fields.Many2one(
        comodel_name="verifactu.map", string="Parent mapping", ondelete="cascade"
    )
