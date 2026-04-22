# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    caser_insurance_ecommerce = fields.Boolean(
        string="Caser Insurance in eCommerce",
        compute="_compute_caser_insurance_ecommerce",
        store=True,
        readonly=False,
        help="Si está activado, este producto podrá asegurarse con Caser "
        "durante el proceso de compra en la tienda online.",
    )

    @api.depends("categ_id.caser_asset_type")
    def _compute_caser_insurance_ecommerce(self):
        for record in self:
            if record.categ_id.caser_asset_type:
                record.caser_insurance_ecommerce = True
            else:
                record.caser_insurance_ecommerce = False

    def get_caser_insurance_price_display(self, price):
        """Return the insurance price display string for the given product price.

        Uses the same price (combination_info['price']) that the website shows
        the customer, consistent with price_reduce_taxinc used in cart/orders.
        """
        self.ensure_one()
        if not self.caser_insurance_ecommerce or not price:
            return ""
        insurance_product = (
            self.env["caser.price.range"]
            .sudo()
            .get_insurance_product_for_price(price, self.categ_id.caser_asset_type)
        )
        return f"{insurance_product.list_price}€" if insurance_product else ""
