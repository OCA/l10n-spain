# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request


class WebsaleCaserInsuranceController(http.Controller):
    @http.route(
        "/shop/caser_insurance/get_uninsured_products",
        type="json",
        auth="public",
        website=True,
    )
    def get_uninsured_products(self):
        if not request.website.caser_insurance_enabled:
            return {"products": []}
        order = request.website.sale_get_order()
        if not order:
            return {"products": []}
        uninsured = []
        for line in order.order_line:
            if (
                line.product_id.product_tmpl_id.caser_insurance_ecommerce
                and not line.caser_insure_quantity
                and not line.is_caser_insurance
            ):
                insurance_product = (
                    request.env["caser.price.range"]
                    .sudo()
                    .get_insurance_product_for_price(
                        line.price_reduce_taxinc,
                        line.product_id.categ_id.caser_asset_type,
                    )
                )
                uninsured.append(
                    {
                        "line_id": line.id,
                        "product_name": line.product_id.name,
                        "quantity": int(line.product_uom_qty),
                        "price": line.price_reduce_taxinc,
                        "insurance_price": insurance_product.list_price
                        if insurance_product
                        else 0,
                        "image_url": (
                            f"/web/image/product.product/"
                            f"{line.product_id.id}/image_128"
                        ),
                    }
                )
        return {"products": uninsured}

    @http.route(
        "/shop/caser_insurance/update_insurance",
        type="json",
        auth="public",
        website=True,
    )
    def update_insurance(self, line_insurances):
        if not request.website.caser_insurance_enabled:
            return {"success": False}
        order = request.website.sale_get_order()
        if not order:
            return {"success": False}
        for line_id, insure_qty in line_insurances.items():
            int_line_id = int(line_id)
            line = order.order_line.filtered(lambda rec, lid=int_line_id: rec.id == lid)
            if line:
                line.caser_insure_quantity = int(insure_qty)
        return {"success": True}
