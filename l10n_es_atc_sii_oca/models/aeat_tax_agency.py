# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.l10n_es_aeat_sii_oca.models.aeat_tax_agency import SII_WDSL_MAPPING


class AeatTaxAgency(models.Model):
    _inherit = "aeat.tax.agency"

    def _atc_sii_zeep_wsdl(self, soap_address):
        """Devuelve la URL WSDL para zeep (CXF expone el WSDL en ``endpoint?wsdl``)."""
        if not soap_address or "?" in soap_address:
            return soap_address
        return f"{soap_address}?wsdl"

    def _connect_params_sii(self, mapping_key, company):
        """Parámetros de conexión ATC: cautela en pruebas y sufijo WSDL para zeep.

        Las URLs almacenadas en la agencia omiten ``?wsdl``; zeep lo necesita
        para obtener el WSDL. La ``address`` SOAP (override de test o binding
        por defecto) se mantiene sin sufijo.
        """
        result = super()._connect_params_sii(mapping_key, company)
        canarias = self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias", raise_if_not_found=False
        )
        if not canarias or self.id != canarias.id:
            return result
        soap_address = result.get("address") or result["wsdl"]
        if company.sii_test:
            wsdl_field = SII_WDSL_MAPPING[mapping_key]
            test_address = getattr(self, f"{wsdl_field}_test_address", None) or ""
            if test_address:
                result["address"] = test_address
                soap_address = test_address
        result["wsdl"] = self._atc_sii_zeep_wsdl(soap_address)
        return result
