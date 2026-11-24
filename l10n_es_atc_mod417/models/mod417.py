# Copyright 2023 Binhex - Nicolás Ramos
# Copyright 2024 Binhex - Christian Ramos
# Copyright 2025 Tecnativa - Carlos Lopez
# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl

from odoo import models

from odoo.addons.l10n_es_atc.models.l10n_es_atc_report import ATC_JAR_URL

ATC_JAR_URL["417"] = (
    "https://www3.gobiernodecanarias.org/tributos/atc/documents/d/agencia-tributaria-canaria/m417v231e26-zip-1"
)


class L10nEsAtcmod417Report(models.Model):
    """Monthly self-assessment of the IGIC: the boxes, the result and the
    checks of the quarterly model 420, filed with its own ATC program."""

    _inherit = "l10n.es.atc.mod420.report"
    _name = "l10n.es.atc.mod417.report"
    _description = "ATC 417 Report"
    _aeat_number = "417"
    _period_quarterly = False
    _period_monthly = True
    _period_yearly = False

    def action_generar_mod417(self):
        self.ensure_one()
        self._atc_validate_fields()
        report_name = "l10n_es_atc_mod417.mod417_report_xml"
        # the jar filename to be used from .zip
        # downloaded from the url in ATC_JAR_URL
        jar_filename = "pa-mod417.jar"
        # the main class to be used from the jar file
        main_class = "org.grecasa.ext.pa.mod417.MIModelo417"
        # The filename of the report that the user will download
        filename = f"modelo{self._aeat_number}"
        # run the command and get the attachment
        attachment = self._atc_run_cmd(report_name, filename, jar_filename, main_class)
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
        }
