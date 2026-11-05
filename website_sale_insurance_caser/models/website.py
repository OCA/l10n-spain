# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    caser_insurance_enabled = fields.Boolean(
        string="Caser Insurance",
        help="Enable Caser insurance on this website's eCommerce. "
        "When disabled, the insurance checkbox on the product page "
        "and the checkout insurance modal will not be shown.",
    )
