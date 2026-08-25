# Copyright 2025 Factor Libre - Almudena de La Puente <almudena.delapuente@factorlibre.es>  # noqa: E501
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class VerifactuMixin(models.AbstractModel):
    _inherit = "verifactu.mixin"

    @api.model
    def _get_verifactu_taxes_map(self, codes, date):
        """Inject OSS taxes when querying not subjected invoices."""
        taxes = super()._get_verifactu_taxes_map(codes, date)
        if any([map_code == "N2" for map_code in codes]):
            taxes |= self.env["account.tax"].search(
                [
                    ("oss_country_id", "!=", False),
                    ("company_id", "in", [False, self.company_id.id]),
                ]
            )
        return taxes

    def _check_all_taxes_mapped(self):
        """Consider OSS taxes as mapped for VERI*FACTU."""
        if super()._check_all_taxes_mapped():
            return True
        # Fallback: check if all taxes are either mapped or OSS
        tax_lines = self._get_aeat_tax_info()
        if not tax_lines:
            return False
        verifactu_map = self._get_verifactu_map(self._get_document_date())
        tax_xml_ids = verifactu_map.map_lines.tax_xmlid_ids.mapped("name")
        mapped_taxes = self.company_id._get_taxes_from_xmlids(tax_xml_ids)
        # Add OSS taxes to mapped set
        oss_taxes = self.env["account.tax"].search(
            [
                ("oss_country_id", "!=", False),
                ("company_id", "in", [False, self.company_id.id]),
            ]
        )
        mapped_taxes |= oss_taxes
        for tax_line in tax_lines.values():
            if tax_line["tax"] not in mapped_taxes:
                return False
        return True


class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_all_taxes_mapped(self):
        """Consider OSS taxes as mapped for VERI*FACTU (account.move)."""
        if super()._check_all_taxes_mapped():
            return True
        tax_lines = self._get_aeat_tax_info()
        if not tax_lines:
            return False
        verifactu_map = self._get_verifactu_map(self._get_document_date())
        tax_xml_ids = verifactu_map.map_lines.tax_xmlid_ids.mapped("name")
        mapped_taxes = self.company_id._get_taxes_from_xmlids(tax_xml_ids)
        oss_taxes = self.env["account.tax"].search(
            [
                ("oss_country_id", "!=", False),
                ("company_id", "in", [False, self.company_id.id]),
            ]
        )
        mapped_taxes |= oss_taxes
        for tax_line in tax_lines.values():
            if tax_line["tax"] not in mapped_taxes:
                return False
        return True
