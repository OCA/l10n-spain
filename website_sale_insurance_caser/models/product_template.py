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
        help="If enabled, this product can be insured with Caser during the "
        "checkout process in the online shop.",
    )

    @api.depends(
        "categ_id.caser_asset_type",
        "product_brand_id.caser_mobile_code",
        "product_brand_id.caser_tablet_code",
    )
    def _compute_caser_insurance_ecommerce(self):
        # Insurable only if the brand has the Caser code for the category's asset
        # type; otherwise the policy would fail at delivery (brand not admitted).
        for record in self:
            asset_type = record.categ_id.caser_asset_type
            record.caser_insurance_ecommerce = bool(
                asset_type and record.product_brand_id._get_caser_code(asset_type)
            )

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
