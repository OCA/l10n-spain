from odoo import _, api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def create(self, values):
        if self._context.get("generated2uploaded"):
            order = self.env["account.payment.order"].browse(
                values.get("payment_order_id")
            )
            if (
                not order.payment_mode_id.cancel_risk
                or not order.payment_type == "inbound"
            ):
                return super().create(values)
            commercial_effects_id = (
                order.payment_mode_id.discounted_commercial_effects_id
            )
            debit_effects_id = order.payment_mode_id.debit_discounted_effects_id
            for line in values.get("line_ids", []):
                ll = line[2]
                bank_line = self.env["bank.payment.line"].browse(
                    ll.get("bank_payment_line_id")
                )
                if ll["account_id"] == commercial_effects_id.id:
                    ll.update(
                        {
                            "name": _("(Cancelled risk) %s") % values.get("ref", ""),
                            "date_maturity": bank_line.date,
                        }
                    )
                    continue
                else:
                    ll.update(
                        {
                            "account_id": debit_effects_id.id,
                            "name": _("(Cancelled risk) %s") % values.get("ref", ""),
                            "date_maturity": bank_line.date,
                        }
                    )
        return super().create(values)
