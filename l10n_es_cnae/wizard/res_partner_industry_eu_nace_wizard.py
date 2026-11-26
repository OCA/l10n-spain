# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# Copyright 2026 Moduon Team S.L. <info@moduon.team>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import csv

from odoo import api, models
from odoo.tools import file_open


class ResPartnerIndustryEUNaceWizard(models.TransientModel):
    _inherit = "res.partner.industry.eu.nace.wizard"

    @api.model
    def create_spanish_industries(self):
        """Create the CNAE 2025 subclasses, or update their names."""
        industry_model = self.env["res.partner.industry"].with_context(lang="en_US")
        nace = industry_model._get_nace_map()
        cnae = industry_model._get_nace_map("cnae2025")
        spanish = self.env["res.lang"]._lang_get("es_ES")
        created = industry_model
        with file_open("l10n_es_cnae/data/res.partner.industry.csv") as csvfile:
            for _xmlid, parent_code, code, name, name_es, _cnae2009 in csv.reader(
                csvfile
            ):
                vals = {
                    "name": name,
                    "full_name": f"{code} - {name}",
                    "parent_id": nace.get(parent_code, False),
                }
                industry = industry_model.browse(cnae.get(code))
                if industry:
                    if not vals["parent_id"]:
                        del vals["parent_id"]
                    industry.write(vals)
                else:
                    industry = industry_model.create(
                        dict(vals, nace_codes={"cnae2025": code})
                    )
                    created |= industry
                if spanish:
                    industry.with_context(lang="es_ES").write(
                        {"name": name_es, "full_name": f"{code} - {name_es}"}
                    )
        return created

    def _create_nace_industry(self, nace_data, languages):
        # After the NACE Rev. 2.1 industries, which are their parents
        nace_ids = super()._create_nace_industry(nace_data, languages)
        return nace_ids | self.create_spanish_industries()

    def update_partner_industry_eu_nace(self):
        # Rename the CNAE 2009 subclasses first: NACE Rev. 2.1 may give their old
        # name to a sibling, e.g. 59.13 takes the old Spanish name of 59.17
        self.create_spanish_industries()
        return super().update_partner_industry_eu_nace()
