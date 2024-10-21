# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, models


class Mod592XlsxManufacturer(models.AbstractModel):
    _name = "report.l10n_es_aeat_mod592.l10n_es_aeat_mod592_xlsx_man"
    _description = "Mod592 XLSX Manufacturer"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, objects):
        mod592 = objects[0]
        sheet = workbook.add_worksheet(_("Manufacturer Items"))
        # header
        model = self.env["l10n.es.aeat.mod592.report.line.manufacturer"]
        next_col = 0
        for info_key in model._get_csv_report_header():
            sheet.write(0, next_col, info_key)
            next_col += 1
        # content
        next_row = 1
        for obj in mod592.manufacturer_line_ids:
            next_col = 0
            for val_item in obj._get_csv_report_info_values():
                sheet.write(next_row, next_col, val_item)
                next_col += 1
            next_row += 1


class Mod592XlsxAcquirer(models.AbstractModel):
    _name = "report.l10n_es_aeat_mod592.l10n_es_aeat_mod592_xlsx_acquirer"
    _description = "Mod592 XLSX Acquirer"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, objects):
        mod592 = objects[0]
        sheet = workbook.add_worksheet(_("Acquirer Items"))
        # header
        model = self.env["l10n.es.aeat.mod592.report.line.acquirer"]
        next_col = 0
        for info_key in model._get_csv_report_header():
            sheet.write(0, next_col, info_key)
            next_col += 1
        # content
        next_row = 1
        for obj in mod592.acquirer_line_ids:
            next_col = 0
            for val_item in obj._get_csv_report_info_values():
                sheet.write(next_row, next_col, val_item)
                next_col += 1
            next_row += 1
