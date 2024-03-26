# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "sigaus.mixin"]

    _sigaus_secondary_unit_fields = {
        "line_ids": "order_line",
        "date_field": "date_order",
        "editable_states": ["draft", "sent"],
    }

    @api.depends("company_id", "fiscal_position_id")
    def _compute_is_sigaus(self):
        return super()._compute_is_sigaus()

    @api.depends("is_sigaus", "date_order", "company_id")
    def _compute_sigaus_is_date(self):
        return super()._compute_sigaus_is_date()

    @api.depends("company_id")
    def _compute_sigaus_company(self):
        return super()._compute_sigaus_company()

    @api.depends("order_line")
    def _compute_sigaus_has_line(self):
        return super()._compute_sigaus_has_line()

    def _get_sigaus_line_vals(self, lines=False, **kwargs):
        sigaus_vals = super()._get_sigaus_line_vals(lines, **kwargs)
        sigaus_vals["order_id"] = self.id
        if self.order_line:
            sigaus_vals["sequence"] = self.order_line[-1].sequence + 1
        if sigaus_vals.get("invoice_lines"):
            sigaus_vals["date_planned"] = (
                self.env["purchase.order.line"]
                ._get_date_planned(False)
                .strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            )
        return sigaus_vals

    def apply_sigaus(self):
        for rec in self.filtered(
            lambda a: a.is_sigaus and a.sigaus_is_date and a.state in ["draft", "sent"]
        ):
            sigaus_vals = rec._get_sigaus_line_vals()
            self.env["purchase.order.line"].create(sigaus_vals)

    def action_create_invoice(self):
        obj = self.with_context(from_purchase=True)
        return super(PurchaseOrder, obj).action_create_invoice()

    def write(self, vals):
        res = super(PurchaseOrder, self.with_context(avoid_recursion=True)).write(vals)
        sigaus_purchases = self.filtered(
            lambda a: a.is_sigaus
            and a.sigaus_is_date
            and any(
                line.product_id.sigaus_has_amount
                for line in a.order_line.filtered("product_id")
            )
        )
        for purchase in sigaus_purchases.filtered("id"):
            if self.env.context.get("avoid_recursion"):
                continue
            purchase.automatic_sigaus_exception()
            purchase.apply_sigaus()
        (self - sigaus_purchases).filtered(
            lambda a: (
                not a.is_sigaus
                or not any(
                    line.product_id.sigaus_has_amount
                    for line in a.order_line.filtered("product_id")
                )
            )
            and a.sigaus_has_line
        )._delete_sigaus()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        purchases = super().create(vals_list)
        for purchase in purchases.filtered(
            lambda a: a.is_sigaus
            and a.sigaus_is_date
            and any(
                line.product_id.sigaus_has_amount
                for line in a.order_line.filtered("product_id")
            )
        ):
            purchase.automatic_sigaus_exception()
            purchase.apply_sigaus()
        return purchases

    def copy(self, default=None):
        # Do not calculate SIGAUS through create method in purchase.order.lines
        # but calculate it through create method in purchase.order
        new_po = super(PurchaseOrder, self.with_context(avoid_recursion=True)).copy(
            default
        )
        return new_po
