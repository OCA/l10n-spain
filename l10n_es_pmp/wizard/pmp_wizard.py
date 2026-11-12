# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class L10nEsPmpWizard(models.TransientModel):
    _name = "l10n.es.pmp.wizard"
    _description = "Wizard for the Average Payment Period to Suppliers (PMP)"

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Done"),
        ],
        default="draft",
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)

    # Results
    total_payments_made = fields.Monetary(currency_field="currency_id")
    total_pending_payments = fields.Monetary(currency_field="currency_id")
    ratio_paid_operations = fields.Float(string="Ratio of Paid Operations (days)")
    ratio_pending_operations = fields.Float(string="Ratio of Pending Operations (days)")
    pmp = fields.Float(string="Average Payment Period (days)")

    # Crea y Crece Law
    volume_paid_in_term = fields.Monetary(
        string="Monetary Volume Paid in Legal Term", currency_field="currency_id"
    )
    pct_volume_paid_in_term = fields.Float(string="% over total monetary")
    invoices_paid_in_term = fields.Integer(
        string="Number of Invoices Paid in Legal Term"
    )
    pct_invoices_paid_in_term = fields.Float(string="% over total invoices")

    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")

    def action_calculate(self):
        self.ensure_one()

        domain = [
            ("company_id", "=", self.company_id.id),
            ("move_id.move_type", "in", ("in_invoice", "in_refund", "in_receipt")),
            ("account_id.account_type", "=", "liability_payable"),
            ("parent_state", "=", "posted"),
        ]
        aml_obj = self.env["account.move.line"]
        invoice_lines = aml_obj.search(domain)

        sum_payments = 0.0
        sum_days_payments = 0.0
        volume_paid_in_term = 0.0

        paid_invoices_in_period = {}

        # Paid Operations
        for line in invoice_lines:
            partials = line.matched_debit_ids + line.matched_credit_ids
            for partial in partials:
                payment_date = partial.max_date
                if not (self.date_start <= payment_date <= self.date_end):
                    continue

                invoice_date = line.move_id.invoice_date or line.move_id.date
                days_payment = (payment_date - invoice_date).days

                amount_paid = partial.amount
                if line == partial.debit_move_id:
                    amount_paid = -amount_paid

                sum_payments += amount_paid
                sum_days_payments += amount_paid * days_payment

                if days_payment <= 60:
                    volume_paid_in_term += amount_paid

                if line.move_id.id not in paid_invoices_in_period:
                    paid_invoices_in_period[line.move_id.id] = days_payment
                else:
                    if days_payment > paid_invoices_in_period[line.move_id.id]:
                        paid_invoices_in_period[line.move_id.id] = days_payment

        invoices_paid = len(paid_invoices_in_period)
        invoices_paid_in_term = sum(
            1 for days in paid_invoices_in_period.values() if days <= 60
        )

        rop = (sum_days_payments / sum_payments) if sum_payments else 0.0

        # Pending Operations
        sum_pending = 0.0
        sum_days_pending = 0.0

        for line in invoice_lines:
            invoice_date = line.move_id.invoice_date or line.move_id.date
            if invoice_date > self.date_end:
                continue

            signed_amount = line.balance
            partials = line.matched_debit_ids + line.matched_credit_ids
            for partial in partials:
                if partial.max_date <= self.date_end:
                    if line == partial.credit_move_id:
                        signed_amount += partial.amount
                    else:
                        signed_amount -= partial.amount

            residual = -signed_amount
            residual = (
                line.currency_id.round(residual) if line.currency_id else residual
            )

            if abs(residual) > 0.01:
                days_pending = (self.date_end - invoice_date).days
                sum_pending += residual
                sum_days_pending += residual * days_pending

        ropp = (sum_days_pending / sum_pending) if sum_pending else 0.0

        total_payments_made = sum_payments
        total_pending_payments = sum_pending

        pmp_val = 0.0
        den = total_payments_made + total_pending_payments
        if den:
            pmp_val = (
                (rop * total_payments_made) + (ropp * total_pending_payments)
            ) / den

        pct_vol = (
            (volume_paid_in_term / total_payments_made * 100)
            if total_payments_made
            else 0.0
        )
        pct_fac = (
            (invoices_paid_in_term / invoices_paid * 100) if invoices_paid else 0.0
        )

        self.write(
            {
                "state": "done",
                "total_payments_made": total_payments_made,
                "total_pending_payments": total_pending_payments,
                "ratio_paid_operations": rop,
                "ratio_pending_operations": ropp,
                "pmp": pmp_val,
                "volume_paid_in_term": volume_paid_in_term,
                "pct_volume_paid_in_term": pct_vol,
                "invoices_paid_in_term": invoices_paid_in_term,
                "pct_invoices_paid_in_term": pct_fac,
            }
        )

        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Average Payment Period to Suppliers (PMP)"),
            "res_model": "l10n.es.pmp.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_print(self):
        # We can implement a PDF report later, for now we just show it on screen.
        return self.action_calculate()
