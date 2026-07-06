# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models


class L10nEsPaymentPeriodReportXlsx(models.AbstractModel):
    _name = "report.l10n_es_payment_period_report.payment_period_report_xlsx"
    _description = "Spanish supplier payment period report XLSX"
    _inherit = "report.account_financial_report.abstract_report_xlsx"

    def generate_xlsx_report(self, workbook, data, objects):
        if objects.computed_method != objects.method:
            objects.action_compute()
        return super().generate_xlsx_report(workbook, data, objects)

    def _get_selection_label(self, record, field_name, value=None):
        selection = record._fields[field_name]._description_selection(record.env)
        return dict(selection).get(record[field_name] if value is None else value, "")

    def _get_report_name(self, report, data=False):
        return self._get_report_complete_name(
            report, _("Supplier Payment Period Report")
        )

    def _get_report_columns(self, report):
        if report.computed_method == "abbreviated":
            return {
                0: {"header": _("Concept"), "field": "label", "width": 45},
                1: {"header": _("Value"), "field": "value", "width": 18},
            }
        return {
            0: {"header": _("Type"), "field": "line_type", "width": 16},
            1: {"header": _("Invoice"), "field": "move", "width": 20},
            2: {"header": _("Payment entry"), "field": "payment_move", "width": 20},
            3: {"header": _("Supplier"), "field": "partner", "width": 35},
            4: {"header": _("Start date"), "field": "date_start", "width": 12},
            5: {"header": _("Payment date"), "field": "payment_date", "width": 12},
            6: {"header": _("Amount"), "field": "amount", "width": 16},
            7: {"header": _("Days"), "field": "days", "width": 8},
            8: {"header": _("Within legal period"), "field": "within", "width": 12},
        }

    def _get_report_filters(self, report):
        filters = [
            [_("Fiscal year"), str(report.year)],
            [_("Date from"), report.date_from.strftime("%d/%m/%Y")],
            [_("Date to"), report.date_to.strftime("%d/%m/%Y")],
            [
                _("Method"),
                self._get_selection_label(report, "method", report.computed_method),
            ],
        ]
        if report.computed_method == "normal":
            filters += [
                [_("Legal payment days"), str(report.legal_payment_days)],
                [_("Start date"), self._get_selection_label(report, "date_start_type")],
            ]
        return filters

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 2

    def _write_summary(self, title, rows, report_data):
        """Write label/value rows, the value under the amount column."""
        sheet = report_data["sheet"]
        formats = report_data["formats"]
        value_col = 6 if len(report_data["columns"]) > 2 else 1
        self.write_array_title(title, report_data)
        for label, value, format_name in rows:
            row = report_data["row_pos"]
            if value_col > 1:
                sheet.merge_range(row, 0, row, value_col - 1, label)
            else:
                sheet.write_string(row, 0, label)
            sheet.write_number(
                row, value_col, value, format_name and formats[format_name] or None
            )
            report_data["row_pos"] += 1
        report_data["row_pos"] += 1

    def _generate_report_content(self, workbook, report, data, report_data):
        title = _("Average payment period to suppliers")
        rows = [
            (
                _("Average payment period to suppliers (days)"),
                report.average_payment_period,
                "format_amount",
            )
        ]
        if report.computed_method == "abbreviated":
            rows += [
                (
                    _("Trade creditors opening balance"),
                    report.creditor_opening_balance,
                    "format_amount",
                ),
                (
                    _("Trade creditors closing balance"),
                    report.creditor_closing_balance,
                    "format_amount",
                ),
                (
                    _("Average trade creditors balance"),
                    report.creditor_average_balance,
                    "format_amount",
                ),
                (_("Net purchases"), report.net_purchases, "format_amount"),
                (_("External services"), report.external_services, "format_amount"),
            ]
            self._write_summary(title, rows, report_data)
            return
        rows += [
            (
                _("Ratio of paid operations (days)"),
                report.paid_operations_ratio,
                "format_amount",
            ),
            (
                _("Ratio of operations pending payment (days)"),
                report.pending_operations_ratio,
                "format_amount",
            ),
            (_("Total payments made"), report.total_amount_paid, "format_amount"),
            (_("Total payments pending"), report.total_amount_pending, "format_amount"),
        ]
        self._write_summary(title, rows, report_data)
        self._write_summary(
            _("Payments within %s days") % report.legal_payment_days,
            [
                (
                    _("Monetary volume"),
                    report.total_amount_paid_within,
                    "format_amount",
                ),
                (
                    _("Percentage of total payments"),
                    report.amount_within_percent / 100,
                    "format_percent_bold_italic",
                ),
                (_("Number of invoices"), report.invoice_count_within, False),
                (
                    _("Percentage of total invoices"),
                    report.invoice_within_percent / 100,
                    "format_percent_bold_italic",
                ),
            ],
            report_data,
        )
        self.write_array_header(report_data)
        for line in report.line_ids:
            self._write_detail_line(line, report_data)

    def _write_detail_line(self, line, report_data):
        sheet = report_data["sheet"]
        row = report_data["row_pos"]
        texts = [
            self._get_selection_label(line, "line_type"),
            line.move_id.name or "",
            line.payment_move_id.name or "",
            line.partner_id.display_name or "",
            line.date_start.strftime("%d/%m/%Y"),
            line.payment_date.strftime("%d/%m/%Y") if line.payment_date else "",
        ]
        for col, text in enumerate(texts):
            sheet.write_string(row, col, text)
        sheet.write_number(row, 6, line.amount, report_data["formats"]["format_amount"])
        sheet.write_number(row, 7, line.days)
        sheet.write_string(row, 8, _("Yes") if line.within_legal_period else _("No"))
        report_data["row_pos"] += 1
