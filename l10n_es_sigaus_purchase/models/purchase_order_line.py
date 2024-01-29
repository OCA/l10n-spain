# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = ["purchase.order.line", "sigaus.line.mixin"]

    _sigaus_secondary_unit_fields = {
        "parent_id": "order_id",
        "date_field": "date_order",
        "qty_field": "product_qty",
        "uom_field": "product_uom",
        "invoice_lines_field": "invoice_lines",
    }

    def _prepare_account_move_line(self, move=False):
        """Transfer SIGAUS value from POL to invoice."""
        res = super()._prepare_account_move_line(move)
        res["is_sigaus"] = self.is_sigaus
        return res
