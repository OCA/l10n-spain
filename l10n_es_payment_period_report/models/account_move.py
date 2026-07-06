# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _l10n_es_payment_period_report_base_date_sql(self, date_start_type):
        if date_start_type == "date":
            return "am.date"
        if date_start_type == "invoice_date_due":
            return "COALESCE(am.invoice_date_due, am.invoice_date, am.date)"
        return "COALESCE(am.invoice_date, am.date)"

    def _l10n_es_payment_period_report_query(
        self, company, date_from, date_to, legal_payment_days=60, date_start_type=False
    ):
        """Return paid supplier invoices fully settled in the selected period.

        The settlement date is reconstructed from account.partial.reconcile.max_date
        over payable move lines. This covers regular payments, partial/multiple
        payments, credit notes and manual reconciliations.
        """
        date_start_sql = self._l10n_es_payment_period_report_base_date_sql(
            date_start_type
        )
        self.flush(
            [
                "name",
                "ref",
                "partner_id",
                "invoice_date",
                "invoice_date_due",
                "date",
                "amount_total_signed",
                "company_id",
                "state",
                "move_type",
            ]
        )
        self.env["account.move.line"].flush(
            ["move_id", "account_id", "company_id", "full_reconcile_id"]
        )
        self.env["account.account"].flush(["internal_type"])
        self.env["account.partial.reconcile"].flush(
            ["debit_move_id", "credit_move_id", "max_date"]
        )
        self.env.cr.execute(
            f"""
            WITH matched_lines AS (
                SELECT debit_move_id AS line_id, max_date
                  FROM account_partial_reconcile
                UNION ALL
                SELECT credit_move_id AS line_id, max_date
                  FROM account_partial_reconcile
            ),
            payable_lines AS (
                SELECT aml.move_id,
                       BOOL_AND(aml.full_reconcile_id IS NOT NULL) AS fully_reconciled,
                       MAX(ml.max_date) AS payment_date
                  FROM account_move_line aml
                  JOIN account_account aa ON aa.id = aml.account_id
             LEFT JOIN matched_lines ml ON ml.line_id = aml.id
                 WHERE aa.internal_type = 'payable'
                   AND aml.company_id = %(company_id)s
              GROUP BY aml.move_id
            ),
            paid_invoices AS (
                SELECT am.id,
                       am.name,
                       am.ref,
                       am.partner_id,
                       am.invoice_date,
                       am.date AS accounting_date,
                       {date_start_sql} AS date_start,
                       pl.payment_date,
                       ABS(am.amount_total_signed) AS amount_total,
                       pl.payment_date - {date_start_sql} AS payment_days
                  FROM account_move am
                  JOIN payable_lines pl ON pl.move_id = am.id
                 WHERE am.company_id = %(company_id)s
                   AND am.state = 'posted'
                   AND am.move_type = 'in_invoice'
                   AND pl.fully_reconciled
                   AND pl.payment_date BETWEEN %(date_from)s AND %(date_to)s
            )
            SELECT pi.id,
                   pi.name,
                   pi.ref,
                   pi.partner_id,
                   rp.name AS partner_name,
                   pi.invoice_date,
                   pi.accounting_date,
                   pi.date_start,
                   pi.payment_date,
                   pi.amount_total,
                   pi.payment_days,
                   pi.payment_days <= %(legal_payment_days)s AS within_legal_period
              FROM paid_invoices pi
         LEFT JOIN res_partner rp ON rp.id = pi.partner_id
          ORDER BY pi.payment_date, pi.id
            """,
            {
                "company_id": company.id,
                "date_from": fields.Date.to_date(date_from),
                "date_to": fields.Date.to_date(date_to),
                "legal_payment_days": legal_payment_days,
            },
        )
        return self.env.cr.dictfetchall()

    def l10n_es_payment_period_report_data(
        self, company, date_from, date_to, legal_payment_days=60, date_start_type=False
    ):
        lines = self._l10n_es_payment_period_report_query(
            company, date_from, date_to, legal_payment_days, date_start_type
        )
        total_amount = sum(line["amount_total"] for line in lines)
        total_within = sum(
            line["amount_total"] for line in lines if line["within_legal_period"]
        )
        invoice_count = len(lines)
        invoice_count_within = len(
            [line for line in lines if line["within_legal_period"]]
        )
        weighted_days = sum(
            line["amount_total"] * line["payment_days"] for line in lines
        )
        return {
            "lines": lines,
            "summary": {
                "total_amount_paid": total_amount,
                "total_amount_paid_within": total_within,
                "invoice_count": invoice_count,
                "invoice_count_within": invoice_count_within,
                "amount_within_percent": total_within / total_amount * 100
                if total_amount
                else 0.0,
                "invoice_within_percent": invoice_count_within / invoice_count * 100
                if invoice_count
                else 0.0,
                "average_payment_period": weighted_days / total_amount
                if total_amount
                else 0.0,
            },
        }
