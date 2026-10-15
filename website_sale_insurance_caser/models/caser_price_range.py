# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64

from odoo import models
from odoo.tools.misc import file_path


class CaserPriceRange(models.Model):
    _inherit = "caser.price.range"

    def _create_or_update_insurance_product(self, price):
        product = super()._create_or_update_insurance_product(price)
        if not product.image_1920:
            img_path = file_path(
                "website_sale_insurance_caser/static/src/img/logo-caser.png"
            )
            if img_path:
                with open(img_path, "rb") as f:
                    product.write({"image_1920": base64.b64encode(f.read())})
        return product
