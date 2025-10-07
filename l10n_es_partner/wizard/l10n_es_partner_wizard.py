# Copyright 2013-2023 Tecnativa - Pedro M. Baeza
# Copyright 2025 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

import codecs
import csv
import logging
import os
import tempfile

from odoo import fields, models, tools

from ..gen_src.gen_data_banks import gen_bank_data_csv

try:
    import xlrd
except ImportError:
    xlrd = None

_logger = logging.getLogger(__name__)


class L10nEsPartnerImportWizard(models.TransientModel):
    _name = "l10n.es.partner.import.wizard"
    _description = "l10n es partner import wizard"

    import_fail = fields.Boolean(default=False)

    def _xls_to_csv(self, xls_path, csv_path):
        if not xlrd:
            _logger.error("La librería `xlrd` no está instalada.")
            return False
        try:
            workbook = xlrd.open_workbook(xls_path)
            sheet = workbook.sheet_by_index(0)
            with codecs.open(csv_path, mode="w", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                for row_num in range(sheet.nrows):
                    writer.writerow(sheet.row_values(row_num))
            return True
        except Exception as e:
            _logger.error(f"Error al convertir XLS a CSV: {e}")
            return False

    def _load_csv_data(self, csv_path):
        fieldnames = [
            "id",
            "name",
            "lname",
            "code",
            "bic",
            "street",
            "street2",
            "website",
            "vat",
            "city",
            "zip",
            "phone",
            "active",
            "state:id",
            "country:id",
        ]

        data = []
        with codecs.open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                data.append(row)

        if data:
            self.env["res.bank"].load(fieldnames, data)

    def import_local(self):
        path = os.path.join("l10n_es_partner", "wizard", "data_banks.csv")
        if path and os.path.exists(path):
            self._load_csv_data(path)
        else:
            _logger.warning("No se encontró el fichero data_banks.csv local.")

    def execute(self):
        import requests

        xls_file, csv_in_file, csv_out_file = None, None, None
        try:
            xls_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xls")
            csv_in_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
            csv_out_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
            xls_file.close()
            csv_in_file.close()

            csv_to_process = ""
            try:
                response = requests.get(
                    "https://www.bde.es/f/webbde/SGE/regis/REGBANESP_CONESTAB_A.xls",
                    timeout=15,
                )
                response.raise_for_status()
                with open(xls_file.name, "wb") as f:
                    f.write(response.content)

                if not self._xls_to_csv(xls_file.name, csv_in_file.name):
                    self.import_fail = True
                    return
                csv_to_process = csv_in_file.name
            except Exception:
                _logger.warning("Error al descargar. Usando fichero local de respaldo.")
                csv_to_process = tools.file_path(
                    "l10n_es_partner/gen_src/REGBANESP_CONESTAB_A.csv"
                )

            gen_bank_data_csv(csv_to_process, csv_out_file.name)

            self._load_csv_data(csv_out_file.name)
            _logger.info("Importación de bancos finalizada correctamente.")
        finally:
            if xls_file:
                os.remove(xls_file.name)
            if csv_in_file:
                os.remove(csv_in_file.name)
            if csv_out_file:
                os.remove(csv_out_file.name)
