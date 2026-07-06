# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def _l10n_es_payment_period_report_account_prefixes(self):
        """Spanish chart of accounts codes in the scope of the report."""
        return {
            # Suppliers (40) and sundry creditors (41) for goods and services,
            # which leaves out fixed asset suppliers (523) or salaries (465)
            "creditor": ["400", "401", "403", "404", "405", "406", "41"],
            "purchase": ["60"],
            "external_service": ["62"],
        }

    @api.model
    def _l10n_es_payment_period_report_account_domain(self, prefixes):
        return expression.OR(
            [[("account_id.code", "=like", f"{prefix}%")] for prefix in prefixes]
        )

    @api.model
    def _l10n_es_payment_period_report_invoice_line_domain(self, company):
        """Payable journal items of the supplier invoices in scope."""
        prefixes = self._l10n_es_payment_period_report_account_prefixes()
        return [
            ("company_id", "=", company.id),
            ("parent_state", "=", "posted"),
            ("move_id.move_type", "in", ["in_invoice", "in_receipt"]),
            ("account_id.internal_type", "=", "payable"),
        ] + self._l10n_es_payment_period_report_account_domain(prefixes["creditor"])

    @api.model
    def _l10n_es_payment_period_report_date_start(self, move, date_start_type):
        if date_start_type == "date":
            return move.date
        return move.invoice_date or move.date

    @api.model
    def _l10n_es_payment_period_report_is_payment(self, counterpart, company):
        """Tell whether a reconciliation counterpart is a material payment.

        Credit notes, other invoices and exchange differences settle the
        invoice without a payment, so they reduce the operation amount instead.
        """
        move = counterpart.move_id
        return (
            not move.is_invoice(include_receipts=True)
            and move.journal_id != company.currency_exchange_journal_id
        )

    @api.model
    def _l10n_es_payment_period_report_line_values(
        self, line, date_start_type, amount, date_end, payment_move=False
    ):
        move = line.move_id
        date_start = self._l10n_es_payment_period_report_date_start(
            move, date_start_type
        )
        return {
            "line_type": "paid" if payment_move else "pending",
            "move_id": move.id,
            "partner_id": move.partner_id.id,
            "invoice_date": move.invoice_date,
            "accounting_date": move.date,
            "date_start": date_start,
            "payment_date": date_end if payment_move else False,
            "payment_move_id": payment_move.id if payment_move else False,
            "amount": amount,
            "days": (date_end - date_start).days,
        }

    @api.model
    def _l10n_es_payment_period_report_paid_lines(
        self, company, date_from, date_to, date_start_type
    ):
        """One value dict per payment made in the period.

        Each partial reconciliation weighs its own amount with its own days, so
        an invoice paid in several instalments is not evaluated as a whole at
        its last payment date.
        """
        line_domain = self._l10n_es_payment_period_report_invoice_line_domain(company)
        partials = self.env["account.partial.reconcile"].search(
            [
                ("company_id", "=", company.id),
                ("max_date", ">=", date_from),
                ("max_date", "<=", date_to),
            ]
            + expression.OR(
                [
                    [
                        (f"{side}.{leaf[0]}", leaf[1], leaf[2])
                        if expression.is_leaf(leaf)
                        else leaf
                        for leaf in line_domain
                    ]
                    for side in ("debit_move_id", "credit_move_id")
                ]
            ),
            order="max_date, id",
        )
        values = []
        for partial in partials:
            if partial.credit_move_id.filtered_domain(line_domain):
                line, counterpart = partial.credit_move_id, partial.debit_move_id
            else:
                line, counterpart = partial.debit_move_id, partial.credit_move_id
            if not self._l10n_es_payment_period_report_is_payment(counterpart, company):
                continue
            values.append(
                self._l10n_es_payment_period_report_line_values(
                    line,
                    date_start_type,
                    partial.amount,
                    partial.max_date,
                    payment_move=counterpart.move_id,
                )
            )
        return values

    @api.model
    def _l10n_es_payment_period_report_pending_lines(
        self, company, date_to, date_start_type
    ):
        """One value dict per invoice still unpaid at the end of the period.

        An invoice is accrued when its start date is not later than the end of
        the period, even if it is posted afterwards. The residual is rebuilt at
        ``date_to`` from the reconciliations done up to that date, as
        ``amount_residual`` reflects today's state.
        """
        lines = self.env["account.move.line"].search(
            self._l10n_es_payment_period_report_invoice_line_domain(company)
            + [
                "|",
                ("date", "<=", date_to),
                ("move_id.invoice_date", "<=", date_to),
                "|",
                "|",
                ("reconciled", "=", False),
                ("matched_debit_ids.max_date", ">", date_to),
                ("matched_credit_ids.max_date", ">", date_to),
            ],
            order="date, id",
        )
        currency = company.currency_id
        values = []
        for line in lines:
            date_start = self._l10n_es_payment_period_report_date_start(
                line.move_id, date_start_type
            )
            if date_start > date_to:
                continue
            settled = sum(
                partial.amount
                for partial in line.matched_debit_ids | line.matched_credit_ids
                if partial.max_date <= date_to
            )
            residual = abs(line.balance) - settled
            if currency.compare_amounts(residual, 0.0) <= 0:
                continue
            values.append(
                self._l10n_es_payment_period_report_line_values(
                    line, date_start_type, residual, date_to
                )
            )
        return values

    @api.model
    def _l10n_es_payment_period_report_normal_data(
        self, company, date_from, date_to, legal_payment_days, date_start_type
    ):
        """Normal annual accounts model (ICAC Resolution 29/01/2016, art. 5.1-5.4).

        Also returns the paid invoices figures required by Law 18/2022.
        """
        paid = self._l10n_es_payment_period_report_paid_lines(
            company, date_from, date_to, date_start_type
        )
        pending = self._l10n_es_payment_period_report_pending_lines(
            company, date_to, date_start_type
        )
        for line in paid + pending:
            line["within_legal_period"] = line["days"] <= legal_payment_days
        total_paid = sum(line["amount"] for line in paid)
        total_pending = sum(line["amount"] for line in pending)
        weighted_paid = sum(line["amount"] * line["days"] for line in paid)
        weighted_pending = sum(line["amount"] * line["days"] for line in pending)
        total_within = sum(
            line["amount"] for line in paid if line["within_legal_period"]
        )
        # An invoice counts as paid within the legal period when every payment
        # it received in the period was.
        invoice_within = {}
        for line in paid:
            invoice_within[line["move_id"]] = (
                invoice_within.get(line["move_id"], True)
                and line["within_legal_period"]
            )
        invoice_count = len(invoice_within)
        invoice_count_within = len([v for v in invoice_within.values() if v])
        total = total_paid + total_pending
        return {
            "lines": paid + pending,
            "summary": {
                "total_amount_paid": total_paid,
                "total_amount_pending": total_pending,
                "paid_operations_ratio": weighted_paid / total_paid
                if total_paid
                else 0.0,
                "pending_operations_ratio": weighted_pending / total_pending
                if total_pending
                else 0.0,
                "average_payment_period": (weighted_paid + weighted_pending) / total
                if total
                else 0.0,
                "total_amount_paid_within": total_within,
                "amount_within_percent": total_within / total_paid * 100
                if total_paid
                else 0.0,
                "invoice_count": invoice_count,
                "invoice_count_within": invoice_count_within,
                "invoice_within_percent": invoice_count_within / invoice_count * 100
                if invoice_count
                else 0.0,
            },
        }

    @api.model
    def _l10n_es_payment_period_report_balance(self, company, prefixes, domain):
        result = self.env["account.move.line"].read_group(
            [("company_id", "=", company.id), ("parent_state", "=", "posted")]
            + self._l10n_es_payment_period_report_account_domain(prefixes)
            + domain,
            ["balance"],
            [],
        )
        return result[0]["balance"] or 0.0

    @api.model
    def _l10n_es_payment_period_report_abbreviated_data(
        self, company, date_from, date_to
    ):
        """Abbreviated annual accounts and SME model (art. 5.5).

        (Average trade creditors / (Net purchases + External services)) x 365
        """
        prefixes = self._l10n_es_payment_period_report_account_prefixes()
        balance = self._l10n_es_payment_period_report_balance
        creditor_opening = -balance(
            company, prefixes["creditor"], [("date", "<", date_from)]
        )
        creditor_closing = -balance(
            company, prefixes["creditor"], [("date", "<=", date_to)]
        )
        period_domain = [("date", ">=", date_from), ("date", "<=", date_to)]
        purchases = balance(company, prefixes["purchase"], period_domain)
        external_services = balance(
            company, prefixes["external_service"], period_domain
        )
        creditor_average = (creditor_opening + creditor_closing) / 2
        expenses = purchases + external_services
        return {
            "lines": [],
            "summary": {
                "creditor_opening_balance": creditor_opening,
                "creditor_closing_balance": creditor_closing,
                "creditor_average_balance": creditor_average,
                "net_purchases": purchases,
                "external_services": external_services,
                "average_payment_period": creditor_average / expenses * 365
                if expenses
                else 0.0,
            },
        }

    @api.model
    def l10n_es_payment_period_report_data(
        self,
        company,
        date_from,
        date_to,
        legal_payment_days=60,
        date_start_type=False,
        method="normal",
    ):
        date_from = fields.Date.to_date(date_from)
        date_to = fields.Date.to_date(date_to)
        if method == "abbreviated":
            return self._l10n_es_payment_period_report_abbreviated_data(
                company, date_from, date_to
            )
        return self._l10n_es_payment_period_report_normal_data(
            company, date_from, date_to, legal_payment_days, date_start_type
        )
