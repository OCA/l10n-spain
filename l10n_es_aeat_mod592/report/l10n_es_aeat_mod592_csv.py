# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import csv

from odoo import models


class Mod592CsvManufacturer(models.AbstractModel):
    _name = "report.l10n_es_aeat_mod592.l10n_es_aeat_mod592_csv_man"
    _description = "Mod592 CSV Manufacturer"
    _inherit = "report.report_csv.abstract"

    def generate_csv_report(self, writer, data, objects):
        mod592 = objects[0]
        writer.writeheader()
        for obj in mod592.manufacturer_line_ids:
            writer.writerow(obj._get_csv_report_info())

    def csv_report_options(self):
        res = super().csv_report_options()
        model = self.env["l10n.es.aeat.mod592.report.line.manufacturer"]
        res["fieldnames"] = model._get_csv_report_header()
        res["delimiter"] = ";"
        res["quoting"] = csv.QUOTE_NONE
        return res


class Mod592CsvAcquirer(models.AbstractModel):
    _name = "report.l10n_es_aeat_mod592.l10n_es_aeat_mod592_csv_acquirer"
    _description = "Mod592 CSV Acquirer"
    _inherit = "report.report_csv.abstract"

    def generate_csv_report(self, writer, data, objects):
        mod592 = objects[0]
        writer.writeheader()
        for obj in mod592.acquirer_line_ids:
            writer.writerow(obj._get_csv_report_info())

    def csv_report_options(self):
        res = super().csv_report_options()
        model = self.env["l10n.es.aeat.mod592.report.line.acquirer"]
        res["fieldnames"] = model._get_csv_report_header()
        res["delimiter"] = ";"
        res["quoting"] = csv.QUOTE_NONE
        return res
