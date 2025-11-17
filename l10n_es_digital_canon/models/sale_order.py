# Copyright 2026 Eduardo Ezerouali - Tecnativa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("partner_id")
    def _compute_partner_shipping_id(self):
        """Override so when partner change recompute taxes"""
        res = super()._compute_partner_shipping_id()
        for order in self:
            order._recompute_taxes()
        return res
