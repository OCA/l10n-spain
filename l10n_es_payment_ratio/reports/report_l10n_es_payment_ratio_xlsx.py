# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, models


class AbstractReportXslx(models.AbstractModel):
    _name = "report.l10n_es_payment_ratio.report_l10n_es_payment_ratio_xlsx"
    _description = "Payment Ratio report XLSX"
    _inherit = "report.report_xlsx.abstract"

    def get_workbook_options(self):
        vals = super().get_workbook_options()
        vals.update({"constant_memory": True})
        return vals

    def _define_formats(self, workbook):
        currency_id = self.env["res.company"]._default_currency_id()
        formats = {
            "format_bold": workbook.add_format({"bold": True}),
            "format_right": workbook.add_format({"align": "right"}),
            "format_left": workbook.add_format({"align": "left"}),
            "format_right_bold_italic": workbook.add_format(
                {"align": "right", "bold": True, "italic": True}
            ),
            "format_header_left": workbook.add_format(
                {"bold": True, "border": True, "bg_color": "#FFFFCC"}
            ),
            "format_header_center": workbook.add_format(
                {"bold": True, "align": "center", "border": True, "bg_color": "#FFFFCC"}
            ),
            "format_header_right": workbook.add_format(
                {"bold": True, "align": "right", "border": True, "bg_color": "#FFFFCC"}
            ),
            "format_header_amount": workbook.add_format(
                {"bold": True, "border": True, "bg_color": "#FFFFCC"}
            ),
            "format_amount": workbook.add_format(),
            "format_amount_bold": workbook.add_format({"bold": True}),
            "format_percent_bold_italic": workbook.add_format(
                {"bold": True, "italic": True}
            ),
        }
        formats["format_amount"].set_num_format(
            "#,##0." + "0" * currency_id.decimal_places
        )
        formats["format_header_amount"].set_num_format(
            "#,##0." + "0" * currency_id.decimal_places
        )
        formats["format_percent_bold_italic"].set_num_format("#,##0.00%")
        formats["format_amount_bold"].set_num_format(
            "#,##0." + "0" * currency_id.decimal_places
        )
        return formats

    def _generate_xlsx_filters(self, sheet, data, objects, formats):
        row = 0
        sheet.write(row, 0, _("Company"), formats["format_header_right"])
        sheet.write(row, 1, data["company_name"], formats["format_left"])
        row += 1
        sheet.write(row, 0, _("Start"), formats["format_header_right"])
        sheet.write(row, 1, data["start_date"], formats["format_left"])
        row += 1
        sheet.write(row, 0, _("End"), formats["format_header_right"])
        sheet.write(row, 1, data["end_date"], formats["format_left"])
        row += 1
        sheet.write(row, 0, _("Total payed amount"), formats["format_header_right"])
        sheet.write(
            row, 1, data["aggregated_data"]["amount_total"], formats["format_amount"]
        )
        row += 1
        sheet.write(row, 0, _("Ratio of payed amount"), formats["format_header_right"])
        if data["aggregated_data"]["amount_total"]:
            sheet.write(
                row,
                1,
                data["aggregated_data"][data["field"]]
                / data["aggregated_data"]["amount_total"],
                formats["format_amount"],
            )
        row += 1
        sheet.write(row, 0, _("Pending amount"), formats["format_header_right"])
        sheet.write(
            row,
            1,
            data["aggregated_data"]["pending_amount_total"],
            formats["format_amount"],
        )
        row += 1
        sheet.write(
            row, 0, _("Ratio of pending payment"), formats["format_header_right"]
        )
        if data["aggregated_data"]["pending_amount_total"]:
            sheet.write(
                row,
                1,
                data["aggregated_data"]["pending_" + data["field"]]
                / data["aggregated_data"]["pending_amount_total"],
                formats["format_amount"],
            )
        row += 1
        sheet.write(row, 0, _("Ratio of payment"), formats["format_header_right"])
        if (
            data["aggregated_data"]["amount_total"]
            + data["aggregated_data"]["pending_amount_total"]
        ):
            sheet.write(
                row,
                1,
                (
                    data["aggregated_data"][data["field"]]
                    + data["aggregated_data"]["pending_" + data["field"]]
                )
                / (
                    data["aggregated_data"]["amount_total"]
                    + data["aggregated_data"]["pending_amount_total"]
                ),
                formats["format_amount"],
            )
        return row

    def _generate_xlsx_report_headers(self, sheet, data, objects, formats, row):
        sheet.write(row, 0, _("Partner"), formats["format_header_left"])
        sheet.write(row, 1, _("Payed amount"), formats["format_header_left"])
        sheet.write(row, 2, _("Ratio of payed amount"), formats["format_header_left"])
        sheet.write(row, 3, _("Pending amount"), formats["format_header_left"])
        sheet.write(row, 4, _("Ratio of pending amount"), formats["format_header_left"])
        sheet.write(row, 5, _("Ratio of payment"), formats["format_header_left"])
        row += 1
        return row

    def _generate_xlsx_report_data(self, sheet, data, objects, formats, row):
        for partner_data in data["data"]:
            if not (
                partner_data["amount_total"]
                + partner_data.get("pending_amount_total", 0)
            ):
                continue
            sheet.write(row, 0, partner_data["partner_id"][1], formats["format_left"])
            sheet.write(row, 1, partner_data["amount_total"], formats["format_amount"])
            if partner_data["amount_total"]:
                sheet.write(
                    row,
                    2,
                    partner_data[data["field"]] / partner_data["amount_total"],
                    formats["format_amount"],
                )
            sheet.write(
                row,
                3,
                partner_data.get("pending_amount_total", 0),
                formats["format_amount"],
            )
            if partner_data.get("pending_amount_total", 0):
                sheet.write(
                    row,
                    4,
                    partner_data.get("pending_" + data["field"], 0)
                    / partner_data.get("pending_amount_total", 0),
                    formats["format_amount"],
                )
            sheet.write(
                row,
                5,
                (
                    partner_data[data["field"]]
                    + partner_data.get("pending_" + data["field"], 0)
                )
                / (
                    partner_data["amount_total"]
                    + partner_data.get("pending_amount_total", 0)
                ),
                formats["format_amount"],
            )
            row += 1
        return row

    def generate_xlsx_report(self, workbook, data, objects):
        formats = self._define_formats(workbook)
        sheet = workbook.add_worksheet("Payment Ratio")
        row = self._generate_xlsx_filters(sheet, data, objects, formats)
        row += 2
        row = self._generate_xlsx_report_headers(sheet, data, objects, formats, row)
        row = self._generate_xlsx_report_data(sheet, data, objects, formats, row)
