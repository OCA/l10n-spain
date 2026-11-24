# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models


class Mod592XlsxManufacturer(models.AbstractModel):
    _name = "report.l10n_es_aeat_mod592.l10n_es_aeat_mod592_xlsx_man"
    _description = "Mod592 XLSX Manufacturer"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, objects):
        mod592 = objects[0]
        sheet = workbook.add_worksheet(self.env._("Manufacturer Items"))
        # header
        model = self.env["l10n.es.aeat.mod592.report.line.manufacturer"]
        for col, info_key in enumerate(model._get_csv_report_header()):
            sheet.write(0, col, info_key)
        # content
        for row, obj in enumerate(mod592.manufacturer_line_ids, start=1):
            for col, val_item in enumerate(obj._get_csv_report_info_values()):
                sheet.write(row, col, val_item)


class Mod592XlsxAcquirer(models.AbstractModel):
    _name = "report.l10n_es_aeat_mod592.l10n_es_aeat_mod592_xlsx_acquirer"
    _description = "Mod592 XLSX Acquirer"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, objects):
        mod592 = objects[0]
        sheet = workbook.add_worksheet(self.env._("Acquirer Items"))
        # header
        model = self.env["l10n.es.aeat.mod592.report.line.acquirer"]
        for col, info_key in enumerate(model._get_csv_report_header()):
            sheet.write(0, col, info_key)
        # content
        for row, obj in enumerate(mod592.acquirer_line_ids, start=1):
            for col, val_item in enumerate(obj._get_csv_report_info_values()):
                sheet.write(row, col, val_item)
