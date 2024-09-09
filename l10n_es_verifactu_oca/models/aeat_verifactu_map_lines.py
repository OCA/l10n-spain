# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AeatVertiactuMapLines(models.Model):
    _name = "aeat.verifactu.map.lines"
    _description = "Aeat Verifactu Map Lines"

    code = fields.Char(required=True)
    name = fields.Char()
    taxes = fields.Many2many(comodel_name="account.tax.template")
    verifactu_map_id = fields.Many2one(
        comodel_name="aeat.verifactu.map",
        string="Aeat Verifactu Map",
        ondelete="cascade",
    )
