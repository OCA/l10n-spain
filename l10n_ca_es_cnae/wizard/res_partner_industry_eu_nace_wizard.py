# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).
import csv
import io
import logging

from odoo import models
from odoo.tools import file_open

from odoo.addons.l10n_es_cnae.hooks import read_cnae2025
from odoo.addons.l10n_eu_nace.hooks import read_nace21

_logger = logging.getLogger(__name__)


class ResPartnerIndustryEUNaceWizard(models.TransientModel):
    _inherit = "res.partner.industry.eu.nace.wizard"

    def _get_industries_with_cnae2009_activity(self):
        """Return ``{code: industry id}`` for the NACE Rev. 2.1 and CNAE 2025
        industries whose code keeps the activity it had in CNAE 2009."""
        industry_model = self.env["res.partner.industry"]
        industries = {}
        for classification, rows in (
            ("nace21", read_nace21()),
            ("cnae2025", read_cnae2025()),
        ):
            nace_map = industry_model._get_nace_map(classification)
            industries.update(
                {
                    row["code"]: nace_map[row["code"]]
                    for row in rows
                    if row["nace2_code"] and row["code"] in nace_map
                }
            )
        return industries

    def spanish_industries_into_catalan(self):
        try:
            with file_open(
                "l10n_ca_es_cnae/data/res.partner.industry.cat.csv", "rb"
            ) as csvfile:
                partner_industry_mod = self.env["res.partner.industry"]
                # These translations are from CNAE 2009: skip the codes that
                # disappear or get another activity in CNAE 2025, e.g. 47.81
                nace_map = self._get_industries_with_cnae2009_activity()
                text_stream = io.TextIOWrapper(csvfile, encoding="utf-8")
                reader = csv.reader(text_stream, delimiter=",", quotechar='"')
                for row in reader:
                    nace_code = row[0]
                    nace_id = nace_map.get(nace_code, False)
                    if nace_id:
                        nace = partner_industry_mod.browse(nace_id)
                        if nace:
                            nace.with_context(lang="ca_ES").write(
                                {
                                    "name": row[1],
                                    "full_name": f"{nace_code} - {row[1]}",
                                }
                            )
        except Exception:
            _logger.exception("Could not read translations to Catalan.")

    def update_partner_industry_eu_nace(self):
        ret_vals = super().update_partner_industry_eu_nace()
        language_codes = self.env["res.lang"].search([]).mapped("code")
        if "ca_ES" in language_codes:
            self.spanish_industries_into_catalan()
        return ret_vals
