# Copyright 2017 FactorLibre - Janire Olagibel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class EcoembesMarketType(models.Model):
    _name = "ecoembes.market.type"
    _description = "Market Type"
    _inherit = "abstract.ecoembes.mixin"

    name = fields.Char(string="Market type")
    reference = fields.Char(string="Abbreviation")

    @api.constrains("reference")
    def _check_reference(self):
        """Override the constraint here to allow non-digit characters in reference"""
        return
