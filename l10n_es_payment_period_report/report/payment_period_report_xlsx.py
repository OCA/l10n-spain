# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class L10nEsPaymentPeriodReportXlsx(models.AbstractModel):
    _name = "report.l10n_es_payment_period_report.payment_period_report_xlsx"
    _description = "Spanish supplier payment period report XLSX"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, wizards):
        for wizard in wizards:
            if not wizard.line_ids:
                wizard.action_compute()
            self._generate_wizard_sheet(workbook, wizard)

    def _generate_wizard_sheet(self, workbook, wizard):
        sheet = workbook.add_worksheet(_("Payments"))
        title_format = workbook.add_format({"bold": True, "font_size": 14})
        header_format = workbook.add_format(
            {"bold": True, "border": 1, "bg_color": "#D9EAF7"}
        )
        amount_format = workbook.add_format({"num_format": "#,##0.00"})
        percent_format = workbook.add_format({"num_format": "0.00%"})
        date_format = workbook.add_format({"num_format": "dd/mm/yyyy"})

        sheet.write(0, 0, _("Supplier Payment Period Report"), title_format)
        sheet.write(2, 0, _("Company"))
        sheet.write(2, 1, wizard.company_id.display_name)
        sheet.write(3, 0, _("Fiscal year"))
        sheet.write(3, 1, wizard.year)
        sheet.write(4, 0, _("Date from"))
        sheet.write(4, 1, fields.Date.to_date(wizard.date_from), date_format)
        sheet.write(5, 0, _("Date to"))
        sheet.write(5, 1, fields.Date.to_date(wizard.date_to), date_format)
        sheet.write(6, 0, _("Legal payment days"))
        sheet.write(6, 1, wizard.legal_payment_days)

        summary_rows = [
            (_("Total amount paid"), wizard.total_amount_paid, amount_format),
            (
                _("Amount paid within legal period"),
                wizard.total_amount_paid_within,
                amount_format,
            ),
            (
                _("Amount within legal period %"),
                wizard.amount_within_percent / 100,
                percent_format,
            ),
            (_("Number of invoices"), wizard.invoice_count, None),
            (
                _("Invoices paid within legal period"),
                wizard.invoice_count_within,
                None,
            ),
            (
                _("Invoices within legal period %"),
                wizard.invoice_within_percent / 100,
                percent_format,
            ),
            (_("Average payment period"), wizard.average_payment_period, None),
        ]
        for row, (label, value, cell_format) in enumerate(summary_rows, start=2):
            sheet.write(row, 3, label)
            sheet.write(row, 4, value, cell_format)

        sheet.merge_range(
            10,
            0,
            10,
            2,
            _("Payments to suppliers within %s days") % wizard.legal_payment_days,
            header_format,
        )
        sheet.write(11, 0, f"{wizard.year}")
        sheet.write(11, 1, _("Amount"), header_format)
        sheet.write(11, 2, "%", header_format)
        sheet.write(12, 0, _("Monetary volume"))
        sheet.write(12, 1, wizard.total_amount_paid_within, amount_format)
        sheet.write(12, 2, wizard.amount_within_percent / 100, percent_format)
        sheet.write(13, 0, _("Number of invoices"))
        sheet.write(13, 1, wizard.invoice_count_within)
        sheet.write(13, 2, wizard.invoice_within_percent / 100, percent_format)

        headers = [
            _("Payment date"),
            _("Invoice"),
            _("Supplier"),
            _("Invoice date"),
            _("Start date"),
            _("Amount"),
            _("Payment days"),
            _("Within legal period"),
        ]
        row = 16
        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)
        for line in wizard.line_ids:
            row += 1
            sheet.write(row, 0, fields.Date.to_date(line.payment_date), date_format)
            sheet.write(row, 1, line.move_id.name or "")
            sheet.write(row, 2, line.partner_id.display_name or "")
            sheet.write(row, 3, fields.Date.to_date(line.invoice_date), date_format)
            sheet.write(row, 4, fields.Date.to_date(line.date_start), date_format)
            sheet.write(row, 5, line.amount_total, amount_format)
            sheet.write(row, 6, line.payment_days)
            sheet.write(row, 7, _("Yes") if line.within_legal_period else _("No"))

        sheet.set_column("A:A", 14)
        sheet.set_column("B:B", 20)
        sheet.set_column("C:C", 35)
        sheet.set_column("D:E", 14)
        sheet.set_column("F:F", 14)
        sheet.set_column("G:H", 18)
        sheet.set_column("D:E", 18)
