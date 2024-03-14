# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = ["sale.order.line", "sigaus.line.mixin"]

    _sigaus_secondary_unit_fields = {
        "parent_id": "order_id",
        "date_field": "date_order",
        "qty_field": "product_uom_qty",
        "uom_field": "product_uom",
        "invoice_lines_field": "invoice_lines",
    }

    def _prepare_invoice_line(self, **optional_values):
        """Transfer SIGAUS value from SOL to invoice."""
        res = super()._prepare_invoice_line(**optional_values)
        res["is_sigaus"] = self.is_sigaus
        return res

    @api.depends("is_sigaus")
    def _compute_invoice_status(self):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        sigaus_lines = self.filtered("is_sigaus")
        for line in sigaus_lines:
            if (
                float_compare(
                    line.qty_invoiced, line.product_uom_qty, precision_digits=precision
                )
                >= 0
            ):
                line.invoice_status = "invoiced"
            else:
                line.invoice_status = "no"
        return super(SaleOrderLine, self - sigaus_lines)._compute_invoice_status()
