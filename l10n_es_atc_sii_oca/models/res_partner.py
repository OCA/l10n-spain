# Copyright 2026 Tecnativa - Carlos Dauden
# Copyright 2026 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.tools import ormcache_context


class ResPartner(models.Model):
    _inherit = "res.partner"

    @ormcache_context("self.vat, self.country_id", keys=("is_canary_tax_agency",))
    def _parse_aeat_vat_info(self):
        # NOTA:
        # El SII-IGIC de la Agencia Tributaria Canaria (ATC) NO admite
        # IDType "02" (NIF-IVA / VAT intracomunitario) del SII estatal AEAT.
        #
        # Aunque la estructura de datos es similar, la ATC no valida operadores
        # intracomunitarios ni registros VIES, porque el IGIC no es IVA.
        #
        # Por ello, los NIF extranjeros deben informarse con IDType "04"
        # ("Documento oficial de identificación") en lugar de "02".
        #
        # Usar IDType "02" provoca el rechazo ATC con error 1103
        # ("Valor del campo IDType incorrecto").
        #
        # Esta conversión es intencionada y obligatoria en envíos SII a la ATC.
        country_code, identifier_type, identifier = super()._parse_aeat_vat_info()
        is_canary_tax_agency = self.env.context.get("is_canary_tax_agency")
        if is_canary_tax_agency and identifier_type == "02":
            identifier_type = "04"
        return country_code, identifier_type, identifier
