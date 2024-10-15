# Copyright 2024 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CompanyPaymentRatioWizard(models.TransientModel):

    _name = "company.payment.ratio.wizard"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    comparison = fields.Selection(
        [
            ("bill_date", "Bill Date"),
            ("create", "Create Date"),
            ("validation", "Accounting Date"),
        ],
        default="bill_date",
    )

    def _get_payed_domain(self):
        return [
            ("payment_date", ">=", self.start_date),
            ("payment_date", "<=", self.end_date),
            ("company_id", "=", self.company_id.id),
            ("state", "=", "posted"),
        ]

    def _get_related_date(self):
        if self.comparison == "bill_date":
            return "invoice_date"
        if self.comparison == "create":
            return "create_date"
        return "date"

    def _get_pending_domain(self):
        return [
            "|",
            ("payment_date", ">", self.end_date),
            ("payment_date", "=", False),
            (self._get_related_date(), "<=", self.end_date),
            ("company_id", "=", self.company_id.id),
            ("state", "=", "posted"),
            ("move_type", "in", ["in_invoice", "in_refund"]),
        ]

    def _get_aggregated_data(self, data):
        return {
            "amount_total": sum(d["amount_total"] for d in data),
            "payment_ratio_%s"
            % self.comparison: sum(
                d["payment_ratio_%s" % self.comparison] for d in data
            ),
            "pending_amount_total": sum(
                d.get("pending_amount_total", 0.0) for d in data
            ),
            "pending_payment_ratio_%s"
            % self.comparison: sum(
                d.get("pending_payment_ratio_%s" % self.comparison, 0.0) for d in data
            ),
        }

    def _prepare_report_data(self):
        data = self._get_partner_data()
        return {
            "res_company_id": self.company_id.id,
            "company_name": self.company_id.name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "comparison": self.comparison,
            "aggregated_data": self._get_aggregated_data(data),
            "data": data,
            "field": "payment_ratio_%s" % self.comparison,
        }

    def _get_partner_data(self):
        raw_data = self.env["account.move"].read_group(
            self._get_payed_domain(),
            [
                "partner_id",
                "amount_total:sum",
                "payment_ratio_%s:sum" % self.comparison,
            ],
            ["partner_id"],
            lazy=False,
        )
        data = {raw["partner_id"][0]: raw for raw in raw_data}
        pending = self.env["account.move"].search(self._get_pending_domain())
        for move in pending:
            data.setdefault(
                move.partner_id.id,
                {
                    "partner_id": [move.partner_id.id, move.partner_id.name],
                    "amount_total": 0.0,
                    "payment_ratio_%s" % self.comparison: 0.0,
                },
            )
            data[move.partner_id.id].setdefault("pending_amount_total", 0.0)
            data[move.partner_id.id].setdefault(
                "pending_payment_ratio_%s" % self.comparison, 0.0
            )
            data[move.partner_id.id][
                "pending_amount_total"
            ] += -move.amount_total_signed
            if self.comparison == "validation":
                difference = (self.end_date - move.date).days
            elif self.comparison == "bill_date":
                difference = (self.end_date - (move.invoice_date or move.date)).days
            else:
                difference = (self.end_date - move.create_date.date()).days
            data[move.partner_id.id]["pending_payment_ratio_%s" % self.comparison] += (
                -move.amount_total_signed * difference
            )
        return list(data.values())

    def _export(self, report_type):
        self.ensure_one()
        data = self._prepare_report_data()
        if report_type == "xlsx":
            report_name = "l10n_es_payment_ratio.report_l10n_es_payment_ratio_xlsx"
        else:
            report_name = "l10n_es_payment_ratio.report_l10n_es_payment_ratio"
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(self.ids, data=data)
        )

    def button_export_html(self):
        self.ensure_one()
        report_type = "qweb-html"
        return self._export(report_type)

    def button_export_pdf(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._export(report_type)
