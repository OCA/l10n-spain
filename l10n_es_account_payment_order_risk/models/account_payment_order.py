from odoo import models, api, fields, _


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    risk_accounting_date = fields.Date(
        string="Accounting date",
    )

    def generated2uploaded(self):
        res = super(
            AccountPaymentOrder, self.with_context(generated2uploaded=True)
        ).generated2uploaded()
        self.move_ids.write({"date": self.risk_accounting_date})
        if self.payment_type == "inbound" and self.payment_mode_id.control_risk:
            for move in self.move_ids.filtered(
                lambda r: any(
                    x.account_id.internal_type == "receivable"
                    for x in r.invoice_line_ids
                )
            ):
                lines = move.invoice_line_ids.filtered(
                    lambda r: r.account_id.internal_type == "receivable"
                )
                if not lines:
                    continue
                if self.payment_mode_id.control_risk:
                    new_move = move.copy(
                        {
                            "invoice_line_ids": False,
                            "payment_order_id": self.id,
                            "ref": _("(Risk) %s") % move.ref or "",
                        }
                    )
                    new_move.line_ids = None
                    lnes = []
                    for line in lines:
                        lnes.append(
                            (
                                0,
                                0,
                                {
                                    "account_id": (
                                        self.payment_mode_id.discounted_commercial_effects_id.id
                                    ),
                                    "partner_id": line.partner_id.id,
                                    "name": new_move.ref,
                                    "debit": line.credit,
                                    "credit": 0,
                                    "date": self.risk_accounting_date,
                                    "date_maturity": line.bank_payment_line_id.date,
                                },
                            )
                        )
                        lnes.append(
                            (
                                0,
                                0,
                                {
                                    "account_id": (
                                        self.payment_mode_id.debit_discounted_effects_id.id
                                    ),
                                    "partner_id": line.partner_id.id,
                                    "name": new_move.ref,
                                    "debit": 0,
                                    "credit": line.credit,
                                    "date": self.risk_accounting_date,
                                    "date_maturity": line.bank_payment_line_id.date,
                                },
                            )
                        )
                    new_move.write({"line_ids": lnes})
                    new_move.post()
        return res
