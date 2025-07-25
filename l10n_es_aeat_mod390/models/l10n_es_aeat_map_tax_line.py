# Copyright 2024 ForgeFlow <contact@forgeflow.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class L10nEsAeatMapTaxLine(models.Model):
    _inherit = "l10n.es.aeat.map.tax.line"

    @api.model
    def _get_redirect_map_lines(self):
        """Get map lines that are redirected to others.
        Return redirect map lines for bankruptcy and uncollectible debt."""
        bankruptcy_map_lines = {
            "aeat_mod390_map_line_31_sale": "aeat_mod390_map_line_29_sale",
            "aeat_mod390_2024_map_line_031_sale": "aeat_mod390_2024_map_line_029_sale",
            "aeat_mod390_map_line_31_purchase": "aeat_mod390_map_line_29_purchase",
            "aeat_mod390_2024_map_line_031_purchase": "aeat_mod390_2024_map_line_029_purchase",  # noqa: E501
            "aeat_mod390_map_line_32_sale": "aeat_mod390_map_line_30_sale",
            "aeat_mod390_2024_map_line_032_sale": "aeat_mod390_2024_map_line_030_sale",
            "aeat_mod390_map_line_32_purchase": "aeat_mod390_map_line_30_purchase",
            "aeat_mod390_2024_map_line_032_purchase": "aeat_mod390_2024_map_line_030_purchase",  # noqa: E501
            "aeat_mod390_map_line_45": "aeat_mod390_map_line_43",
            "aeat_mod390_2024_map_line_045": "aeat_mod390_2024_map_line_043",
            "aeat_mod390_map_line_46": "aeat_mod390_map_line_44",
            "aeat_mod390_2024_map_line_046": "aeat_mod390_2024_map_line_044",
        }
        return bankruptcy_map_lines

    def get_taxes_for_company(self, company):
        """Get taxes from map line, considering redirected map lines (since
        they use exactly the same taxes)."""
        self.ensure_one()
        xml_id = self.get_external_id().get(self.id)
        record_name = xml_id.split(".")[-1] if xml_id else None
        redirect_name = self._get_redirect_map_lines().get(record_name, False)
        if redirect_name:
            redirect_xml_id = f"l10n_es_aeat_mod390.{redirect_name}"
            redirect_map_line = self.env.ref(redirect_xml_id, raise_if_not_found=False)
            if redirect_map_line:
                return super(
                    L10nEsAeatMapTaxLine, redirect_map_line
                ).get_taxes_for_company(company)
        return super().get_taxes_for_company(company)
