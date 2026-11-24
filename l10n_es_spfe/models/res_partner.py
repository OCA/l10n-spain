# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    spfe_exclude = fields.Boolean(
        string="Exclude from SPFE",
        help="Exclude invoices for this partner from mandatory B2B SPFE submission "
        "(e.g. final consumers B2C or excluded entities).",
    )

    def _has_spfe_spanish_nif(self):
        """Return True when the commercial partner has a Spanish NIF."""
        if not self:
            return False
        self.ensure_one()
        commercial = self.commercial_partner_id
        country_code, _id_type, vat_number = commercial._parse_aeat_vat_info()
        raw_vat = (commercial.vat or "").strip().upper()
        if not vat_number and not raw_vat:
            return False
        if raw_vat.startswith("ES"):
            return True
        return bool(
            country_code == "ES"
            and (not commercial.country_id or commercial.country_id.code == "ES")
        )

    def _get_spfe_party_tax_info(self):
        """Return (scheme_id, tax_scheme_id, company_id) for SPFE UBL PartyTaxScheme.

        According to SPFE Anexo I:
        - Spanish NIF (BT-32 / BT-47): TaxScheme/ID='LOC', CompanyID@schemeID='FC',
          and CompanyID contains the 9-char Spanish NIF without 'ES' prefix.
        - EU / VAT ID (BT-31 / BT-48): TaxScheme/ID='VAT', CompanyID@schemeID='VA',
          and CompanyID contains the prefixed VAT number.
        """
        self.ensure_one()
        commercial = self.commercial_partner_id
        country_code, _id_type, vat_number = commercial._parse_aeat_vat_info()
        raw_vat = (commercial.vat or "").strip().upper()
        if not vat_number and not raw_vat:
            raise UserError(
                self.env._(
                    "Partner '%(partner)s' is missing a tax identification number "
                    "(NIF/VAT) required by SPFE.",
                    partner=commercial.display_name,
                )
            )
        if country_code == "ES" or raw_vat.startswith("ES"):
            nif = vat_number or raw_vat[2:]
            return "FC", "LOC", nif.strip().upper()
        vat_full = (
            raw_vat
            if (country_code and raw_vat.startswith(country_code))
            else f"{country_code or ''}{vat_number or raw_vat}"
        )
        return "VA", "VAT", vat_full.strip().upper()
