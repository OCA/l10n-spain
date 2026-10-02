# Copyright 2026 Mike Colangelo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCity(models.Model):
    _inherit = "res.city"

    code = fields.Char(
        help="INE municipality code, required by the ATC tax models "
        "(e.g. 35016 for Las Palmas de Gran Canaria). Up to 19.0 this "
        "field was provided by base_location; it was dropped there, so "
        "this module now carries it."
    )
