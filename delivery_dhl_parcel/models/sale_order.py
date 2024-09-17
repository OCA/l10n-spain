# Copyright 2023 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_delivery_methods(self):
        # Exclude CoD delivery methods when getting methods for checkout in the
        # website_sale_delivery module
        return (
            super()
            ._get_delivery_methods()
            .filtered(lambda c: not c.dhl_parcel_cash_on_delivery)
        )
