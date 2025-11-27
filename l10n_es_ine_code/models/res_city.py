# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCity(models.Model):
    _inherit = "res.city"

    ine_code_id = fields.Many2one(
        comodel_name="res.ine.code",
        string="INE Code",
        help="National Statistics Institute code for this city",
    )
