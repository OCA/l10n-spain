# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).
import csv
import io
import logging

from odoo import models
from odoo.tools import file_open

_logger = logging.getLogger(__name__)


class ResPartnerIndustryEUNaceWizard(models.TransientModel):
    _inherit = "res.partner.industry.eu.nace.wizard"

    def spanish_industries_into_catalan(self):
        try:
            with file_open(
                "l10n_ca_es_cnae/data/res.partner.industry.cat.csv", "rb"
            ) as csvfile:
                partner_industry_mod = self.env["res.partner.industry"]
                all_naces = partner_industry_mod.search_read(
                    [("full_name", "like", " - ")], ["full_name"]
                )
                nace_map = {
                    nace.get("full_name").split(" - ")[0]: nace.get("id")
                    for nace in all_naces
                }
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
