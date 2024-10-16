# Copyright 2017 FactorLibre - Janire Olagibel
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class EcoembesSector(models.Model):
    _name = "ecoembes.sector"
    _description = "Sector"
    _inherit = "abstract.ecoembes.mixin"

    name = fields.Char(string="Sector")
