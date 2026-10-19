# Copyright 2026 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.http import request

from odoo.addons.website_sale.controllers.delivery import Delivery


class WebsiteSaleDelivery(Delivery):
    def _order_summary_values(self, order, **kwargs):
        res = super()._order_summary_values(order, **kwargs)
        canon = sum(
            tax.amount * line.product_uom_qty
            for line in order.website_order_line
            for tax in line.tax_id
            if tax.tax_group_id.name.startswith("Canon digital")
        )
        res["amount_tax"] = request.env["ir.qweb.field.monetary"].value_to_html(
            order.amount_tax - canon, {"display_currency": order.currency_id}
        )
        return res
