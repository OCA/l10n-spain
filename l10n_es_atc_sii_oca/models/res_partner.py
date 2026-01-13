# Copyright 2026 Tecnativa - Carlos Dauden
# Copyright 2026 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.tools import ormcache_context


class ResPartner(models.Model):
    _inherit = "res.partner"

    @ormcache_context("self.vat, self.country_id", keys=("is_canary_tax_agency",))
    def _parse_aeat_vat_info(self):
        # NOTE:
        # The Canary Islands Tax Agency (ATC) SII-IGIC implementation does NOT support
        # IDType "02" (EU VAT number / NIF-IVA) used by the Spanish AEAT SII (VAT).
        #
        # Although the data structure is similar, ATC does not validate intra-community
        # operators nor VIES registrations, since IGIC is not VAT.
        #
        # As a result, foreign VAT numbers must be reported using IDType "04"
        # ("Official identification document") instead of "02".
        #
        # Using IDType "02" causes ATC to reject the record with error code 1103
        # ("Valor del campo IDType incorrecto").
        #
        # This conversion is intentional and required for SII submissions to ATC.
        country_code, identifier_type, identifier = super()._parse_aeat_vat_info()
        is_canary_tax_agency = self.env.context.get("is_canary_tax_agency")
        if is_canary_tax_agency and identifier_type == "02":
            identifier_type = "04"
        return country_code, identifier_type, identifier
