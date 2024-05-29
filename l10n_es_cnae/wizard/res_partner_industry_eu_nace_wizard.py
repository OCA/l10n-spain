# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import models
from odoo.tools import file_open, pycompat

_logger = logging.getLogger(__name__)


class ResPartnerIndustryEUNaceWizard(models.TransientModel):
    _inherit = "res.partner.industry.eu.nace.wizard"

    def update_partner_industry_eu_nace(self):
        ret_vals = super().update_partner_industry_eu_nace()
        try:
            with file_open(
                "l10n_es_cnae/data/res.partner.industry.csv", "rb"
            ) as csvfile:
                reader = pycompat.csv_reader(csvfile, delimiter=",", quotechar='"')
                partner_industry_mod = self.env["res.partner.industry"]
                all_naces = partner_industry_mod.search_read(
                    [("full_name", "like", " - ")], ["full_name"]
                )
                nace_map = {
                    nace.get("full_name").split(" - ")[0]: nace.get("id")
                    for nace in all_naces
                }
                for row in reader:
                    nace_code = row[2]
                    nace_id = nace_map.get(nace_code, False)
                    if not nace_id:
                        vals = {"name": row[3], "full_name": f"{nace_code} - {row[3]}"}
                        parent = nace_map.get(row[1])
                        if parent:
                            vals["parent_id"] = parent
                        partner_industry_mod.create(vals)

        except Exception:
            _logger.exception("Could not create industries from module l10n_es_cnae.")
        return ret_vals
