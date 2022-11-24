from odoo import api, fields, models


class AccountPaymentLineCreate(models.TransientModel):
    _inherit = "account.payment.line.create"

    def _prepare_move_line_domain(self):
        res = super()._prepare_move_line_domain()
        if (
            self.order_id.payment_type == "inbound"
            and self.order_id.payment_mode_id.cancel_risk
        ):
            res.append(
                (
                    "account_id",
                    "=",
                    self.order_id.payment_mode_id.discounted_commercial_effects_id.id,
                )
            )
        return res
