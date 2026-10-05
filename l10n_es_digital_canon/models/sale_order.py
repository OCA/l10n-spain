# Copyright 2026 Eduardo Ezerouali - Tecnativa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _compute_fiscal_position_id(self):
        """Override so when partner or delivery address change recompute taxes"""
        res = super()._compute_fiscal_position_id()
        for order in self.filtered(lambda o: o.state in ("draft", "sent")):
            order._recompute_taxes()
        return res
