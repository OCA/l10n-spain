# Copyright 2013-2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

import logging
import os
import tempfile

from odoo import fields, models, tools

from ..gen_src.gen_data_banks import gen_bank_data_xml

_logger = logging.getLogger(__name__)


class L10nEsPartnerImportWizard(models.TransientModel):
    _name = "l10n.es.partner.import.wizard"
    _description = "l10n es partner import wizard"

    import_fail = fields.Boolean(default=False)

    def import_local(self):
        path = os.path.join("l10n_es_partner", "wizard", "data_banks.xml")
        with tools.file_open(path) as fp:
            tools.convert_xml_import(
                self.env, "l10n_es_partner", fp, {}, "init", noupdate=True
            )

    def execute(self):
        import requests

        src_file = tempfile.NamedTemporaryFile(delete=False)
        dest_file = tempfile.NamedTemporaryFile("w", delete=False)
        try:
            response = requests.get(
                "https://www.bde.es/f/webbde/SGE/regis/REGBANESP_CONESTAB_A.xls",
                timeout=10,
            )
            response.raise_for_status()
            src_file.write(response.content)
            src_file.close()
            src_file_name = src_file.name
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
        ):
            # BDE is forbidding on certain conditions to get the file, so we use a
            # local file. Latest update: 2023-10-07
            log = _logger.warning if tools.config["test_enable"] else _logger.info
            log("Error while downloading data. Using local file.")
            src_file_name = tools.file_path(
                "l10n_es_partner/gen_src/REGBANESP_CONESTAB_A.xls",
            )
        # Generate XML and import it
        gen_bank_data_xml(src_file_name, dest_file.name)
        tools.convert_xml_import(
            self.env, "l10n_es_partner", dest_file.name, {}, "init", noupdate=True
        )
        os.remove(src_file.name)
        os.remove(dest_file.name)
