# Copyright 2019 Tecnativa - Carlos Dauden
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from odoo.api import ormcache
from odoo.fields import Domain


class ResPartner(models.Model):
    _inherit = "res.partner"

    aeat_anonymous_cash_customer = fields.Boolean(
        string="AEAT - Anonymous customer",
        help="Check this for anonymous cash customer. AEAT communication",
    )
    aeat_simplified_invoice = fields.Boolean(
        string="Simplified invoices in AEAT?",
        help="Checking this mark, invoices done to this partner will be "
        "sent to AEAT as simplified invoices.",
    )
    aeat_sending_enabled = fields.Boolean(
        compute="_compute_aeat_sending_enabled",
    )
    real_estate_ids = fields.One2many("l10n.es.aeat.real_estate", "partner_id")

    def _compute_aeat_sending_enabled(self):
        self.aeat_sending_enabled = False

    def _map_aeat_country_code(self, country_code, extended=False):
        """Map country codes according the fiscal conditions.

        :arg boolean extended: If True, it means you want to convert also special
          territories like Overseas France. That ones are not considered for
          intracommunity operations, but they need to use FR country code for
          identification purposes.
        :return: The mapped country code if exists, or the same country code if not.
        """
        country_code_map = {"EL": "GR"}
        if extended:
            country_code_map.update(
                {
                    "RE": "FR",
                    "GP": "FR",
                    "MQ": "FR",
                    "GF": "FR",
                    "PF": "FR",
                    "BL": "FR",
                    "MF": "FR",
                    "PM": "FR",
                    "WF": "FR",
                }
            )
        return country_code_map.get(country_code, country_code)

    def _map_aeat_country_iso_code(self, country_id):
        """Map country ISO code according to AEAT code"""
        code = country_id.code
        country_iso_code_map = {"GR": "EL"}
        return country_iso_code_map.get(code, code)

    @ormcache("self.env")
    def _get_aeat_europe_codes(self):
        europe = self.env.ref("base.europe", raise_if_not_found=False)
        if not europe:
            europe = self.env["res.country.group"].search(
                [Domain("name", "=", "Europe")], limit=1
            )
        return europe.country_ids.mapped("code") + ["XI"]

    def _parse_aeat_vat_info(self):
        """Return tuple with split info (country_code, identifier_type and
        vat_number) from vat and country partner
        """
        self.ensure_one()
        vat_number = self.vat or ""
        prefix = vat_number[:2].upper()
        aeat_country_code = self._map_aeat_country_code(prefix)
        if aeat_country_code in self._get_aeat_europe_codes():
            # Return mapped vats like Greece. Take into account mapped countries
            country_code = aeat_country_code
            vat_number = vat_number[2:]
            identifier_type = (
                "02" if self._check_vat_number(country_code, vat_number) else "04"
            )
        else:
            if self.country_id.code:
                country_code = self.country_id.code
            elif self.env["res.country"].search([Domain("code", "=", prefix)]):
                country_code = prefix
            else:
                country_code = ""
            if (
                self._map_aeat_country_code(country_code)
                in self._get_aeat_europe_codes()
            ):
                # An EU country alone doesn't mean `vat_number` is really a
                # valid intra-community VAT (e.g. an Italian "codice
                # fiscale" for an individual isn't a "partita IVA" and the
                # SII rejects it under IDType 02 with error 1104).
                identifier_type = (
                    "02" if self._check_vat_number(country_code, vat_number) else "04"
                )
            else:
                country_code = self._map_aeat_country_code(country_code, extended=True)
                identifier_type = "04"
        if (
            country_code == "ES"
            and self.has_vat
            and self._check_vat_number("ES", vat_number)
        ):
            identifier_type = ""
            identifier = vat_number
        elif identifier_type == "02":
            identifier = vat_number
        else:
            doc_type, doc = self._l10n_es_get_additional_identifier_type()
            if doc == "NO_DISPONIBLE" or (doc_type == "04" and doc == self.vat):
                return (
                    country_code,
                    "" if country_code == "ES" else identifier_type,
                    vat_number,
                )
            identifier_type, identifier = doc_type, doc
        return (
            country_code,
            identifier_type,
            identifier,
        )

    def _has_valid_aeat_identification(self, allow_alternative_identification=True):
        """Check whether a partner has a valid identification for AEAT reports."""
        self.ensure_one()
        vat = (self.vat or "").strip().upper()
        vat_is_useful = self.has_vat and vat not in ("", "NO_DISPONIBLE")
        if vat_is_useful or not allow_alternative_identification:
            return vat_is_useful
        for identifier in (
            self.l10n_es_passport,
            self.l10n_es_foreign_id,
            self.l10n_es_res_cert,
            self.l10n_es_other_id,
        ):
            if (identifier or "").strip().upper() not in ("", "NO_DISPONIBLE"):
                return True
        return False
