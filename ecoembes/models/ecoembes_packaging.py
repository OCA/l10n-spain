# Copyright 2017 FactorLibre - Janire Olagibel
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class EcoembesPackaging(models.Model):
    _name = "ecoembes.packaging"
    _description = "Packaging"
    _inherit = "abstract.ecoembes.mixin"

    name = fields.Char(string="Packaging")
