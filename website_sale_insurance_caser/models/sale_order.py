# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_update_prices_lines(self):
        return (
            super()
            ._get_update_prices_lines()
            .filtered(lambda line: not line.is_caser_insurance)
        )

    def _cart_update(self, product_id, line_id=None, add_qty=0, set_qty=0, **kwargs):
        if line_id:
            line = self.order_line.filtered(lambda ln: ln.id == line_id)
            if line and line.is_caser_insurance:
                # Insurance lines cannot be increased manually; quantity is
                # managed by _sync_caser_insurance_lines based on caser_insure_quantity.
                if (add_qty or 0) > 0 or (set_qty or 0) > 0:
                    return {"line_id": line_id, "quantity": line.product_uom_qty}
                # For deletions (set_qty=0) or decreases, we handle the removal
                # ourselves instead of calling super(). The cart controller always
                # does browse(line_id) on the returned line_id after _cart_update,
                # so if the line got deleted by then it raises a MissingError.
                # Returning line_id=False skips that browse safely.
                if line.caser_insured_line_id:
                    line.caser_insured_line_id.caser_insure_quantity = max(
                        0, line.caser_insured_line_id.caser_insure_quantity - 1
                    )
                return {"line_id": False, "quantity": 0}
        values = super()._cart_update(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            **kwargs,
        )
        if values.get("line_id") and kwargs.get("caser_insurance_product_page"):
            line = self.env["sale.order.line"].browse(values["line_id"])
            product = self.env["product.product"].browse(product_id)
            if product.product_tmpl_id.caser_insurance_ecommerce:
                insure_qty = (
                    int(line.product_uom_qty)
                    if kwargs.get("caser_add_insurance")
                    else 0
                )
                line.caser_insure_quantity = insure_qty
        return values
