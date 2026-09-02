# Copyright 2026 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    caser_insurance_state = fields.Selection(
        selection=[
            ("no", "No insurance"),
            ("to_send", "Pending"),
            ("error", "Error"),
            ("done", "Insured"),
        ],
        compute="_compute_caser_insurance_state",
        store=True,
    )
    caser_has_error = fields.Boolean(
        compute="_compute_caser_insurance_state",
        store=True,
        index=True,
        string="Caser Insurance Error",
    )
    caser_error = fields.Text(
        compute="_compute_caser_insurance_state",
        store=True,
        string="Caser Insurance Errors",
    )
    caser_insurance_line_ids = fields.One2many(
        comodel_name="sale.order.line",
        compute="_compute_caser_insurance_line_ids",
        string="Caser Insurance Lines",
    )

    @api.depends(
        "order_line.is_caser_insurance",
        "order_line.caser_policy_number",
        "order_line.caser_error_message",
    )
    def _compute_caser_insurance_state(self):
        for order in self:
            lines = order.order_line.filtered("is_caser_insurance")
            errors = lines.filtered("caser_error_message")
            if not lines:
                state = "no"
            elif errors:
                state = "error"
            elif all(line.caser_policy_number for line in lines):
                state = "done"
            else:
                state = "to_send"
            order.caser_insurance_state = state
            order.caser_has_error = state == "error"
            order.caser_error = "\n".join(
                f"• {line.product_id.display_name}: {line.caser_error_message}"
                for line in errors
            )

    @api.depends("order_line.is_caser_insurance")
    def _compute_caser_insurance_line_ids(self):
        for order in self:
            order.caser_insurance_line_ids = order.order_line.filtered(
                "is_caser_insurance"
            )

    def _caser_handle_failure(self, message):
        """Hook on a failed Caser policy: logs it; override to also block/notify."""
        self.ensure_one()
        self.message_post(body=message)
