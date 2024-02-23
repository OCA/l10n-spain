# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import frozendict


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "sigaus.mixin"]

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

    @api.depends("order_line")
    def _compute_sigaus_has_line(self):
        return super()._compute_sigaus_has_line()

    @api.depends("company_id")
    def _compute_company_sigaus(self):
        return super()._compute_company_sigaus()

    def _get_sigaus_line_vals(self, lines=False, **kwargs):
        sigaus_vals = super()._get_sigaus_line_vals(lines, **kwargs)
        sigaus_vals["order_id"] = self.id
        if self.order_line:
            sigaus_vals["sequence"] = self.order_line[-1].sequence + 1
        return sigaus_vals

    def apply_sigaus(self):
        for rec in self.filtered(
            lambda a: a.is_sigaus and a.sigaus_is_date and a.state in ["draft", "sent"]
        ):
            sigaus_vals = rec._get_sigaus_line_vals()
            self.env["sale.order.line"].create(sigaus_vals)

    def write(self, vals):
        res = super().write(vals)
        sigaus_sales = self.filtered(
            lambda a: a.is_sigaus
            and a.sigaus_is_date
            and any(
                line.product_id.sigaus_has_amount
                for line in a.order_line.filtered("product_id")
            )
        )
        for sale in sigaus_sales.filtered("id"):
            if self.env.context.get("avoid_recursion"):
                continue
            sale.automatic_sigaus_exception()
            sale.with_context(avoid_recursion=True).apply_sigaus()
            sale.env.context = frozendict(
                {**sale.env.context, "avoid_recursion": False}
            )
        (self - sigaus_sales).filtered(
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
        sales = super().create(vals_list)
        for sale in sales.filtered(
            lambda a: a.is_sigaus
            and a.sigaus_is_date
            and any(
                line.product_id.sigaus_has_amount
                for line in a.order_line.filtered("product_id")
            )
        ):
            sale.automatic_sigaus_exception()
            sale.apply_sigaus()
        return sales
