# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProductBrand(models.Model):
    _inherit = "product.brand"

    caser_mobile_code = fields.Char(
        string="Caser Code (Mobile)",
        help="Brand code sent to Caser API for mobile phone policies "
        "(asset type 200021)",
    )
    caser_tablet_code = fields.Char(
        string="Caser Code (Tablet)",
        help="Brand code sent to Caser API for tablet policies (asset type 262)",
    )
