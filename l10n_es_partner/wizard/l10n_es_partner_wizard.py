# Copyright 2013-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

import logging
import os
import tempfile

from odoo import _, fields, models, tools

from ..gen_src.gen_data_banks import gen_bank_data_xml

_logger = logging.getLogger(__name__)


class L10nEsPartnerImportWizard(models.TransientModel):
    _name = "l10n.es.partner.import.wizard"
    _inherit = "res.config.installer"
    _description = "l10n es partner import wizard"

    import_fail = fields.Boolean(default=False)

    def import_local(self):
        res = super().execute()
        path = os.path.join("l10n_es_partner", "wizard", "data_banks.xml")
        with tools.file_open(path) as fp:
            tools.convert_xml_import(
                self._cr, "l10n_es_partner", fp, {}, "init", noupdate=True
            )
        return res

    def execute(self):
        import requests

        src_file = tempfile.NamedTemporaryFile(delete=False)
        dest_file = tempfile.NamedTemporaryFile("w", delete=False)
        try:
            response = requests.get(
                "http://www.bde.es/f/webbde/IFI/servicio/regis/ficheros/es/"
                "REGBANESP_CONESTAB_A.XLS"
            )
            response.raise_for_status()
            src_file.write(response.content)
            src_file.close()
            # Generate XML and reopen it
            gen_bank_data_xml(src_file.name, dest_file.name)
            tools.convert_xml_import(
                self._cr, "l10n_es_partner", dest_file.name, {}, "init", noupdate=True
            )
        except requests.exceptions.HTTPError:  # pragma: no cover
            _logger.exception("HTTP Error while importing data")
            self.import_fail = True
            return {
                "name": _("Import spanish bank data"),
                "type": "ir.actions.act_window",
                "res_model": "l10n.es.partner.import.wizard",
                "view_id": self.env.ref(
                    "l10n_es_partner." "l10n_es_partner_import_wizard"
                ).id,
                "view_mode": "form",
                "res_id": self.id,
                "target": "new",
            }
        finally:
            os.remove(src_file.name)
            os.remove(dest_file.name)
