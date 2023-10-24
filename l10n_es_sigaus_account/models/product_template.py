# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sigaus_subject = fields.Selection(
        [("category", "Category"), ("yes", "Yes"), ("no", "No")],
        default="category",
        string="Subject To SIGAUS",
        required=True,
    )
