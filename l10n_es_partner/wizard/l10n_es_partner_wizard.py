# Copyright 2013-2023 Tecnativa - Pedro M. Baeza
# Copyright 2025 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

import csv
import logging
import os
import tempfile

from odoo import fields, models, tools
from odoo.modules.module import get_module_path

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
            with open(csv_path, mode="w", encoding="utf-8", newline="") as csv_file:
                writer = csv.writer(csv_file)
                for row_num in range(sheet.nrows):
                    writer.writerow(sheet.row_values(row_num))
            return True
        except (OSError, ValueError, xlrd.XLRDError) as error:
            _logger.error("Error al convertir XLS a CSV: %s", error)
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
            "state_id:id",
            "country_id:id",
        ]

        with open(csv_path, encoding="utf-8", newline="") as csv_file:
            reader = csv.reader(csv_file)
            next(reader, None)
            data = list(reader)

        if data:
            self.env["l10n.es.bank"].with_context(module="l10n_es_partner").load(
                fieldnames, data
            )

    def import_local(self):
        module_path = get_module_path("l10n_es_partner")
        path = os.path.join(module_path, "wizard", "data_banks.csv")
        if path and os.path.exists(path):
            self._load_csv_data(path)
        else:
            _logger.warning("No se encontró el fichero data_banks.csv local.")

    def execute(self):
        import requests

        with tempfile.TemporaryDirectory() as temp_dir:
            xls_path = os.path.join(temp_dir, "banks.xls")
            csv_in_path = os.path.join(temp_dir, "banks-in.csv")
            csv_out_path = os.path.join(temp_dir, "banks-out.csv")
            csv_to_process = ""
            try:
                response = requests.get(
                    "https://www.bde.es/f/webbde/SGE/regis/REGBANESP_CONESTAB_A.xls",
                    timeout=15,
                )
                response.raise_for_status()
                with open(xls_path, "wb") as bank_file:
                    bank_file.write(response.content)

                if not self._xls_to_csv(xls_path, csv_in_path):
                    self.import_fail = True
                    return
                csv_to_process = csv_in_path
            except requests.RequestException:
                _logger.warning("Error al descargar. Usando fichero local de respaldo.")
                csv_to_process = tools.file_path(
                    "l10n_es_partner/gen_src/REGBANESP_CONESTAB_A.csv"
                )

            gen_bank_data_csv(csv_to_process, csv_out_path)

            self._load_csv_data(csv_out_path)
            _logger.info("Importación de bancos finalizada correctamente.")
