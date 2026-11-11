# Copyright 2025 Sistema de datos - Mario Montes
# Copyright 2025 Tecnativa - Sergio Teruel
import logging

from odoo import api, models

from odoo.addons.l10n_es_aeat.models.aeat_mixin import round_by_keys

_logger = logging.getLogger(__name__)

# Keys of the AEAT SII dictionary that have another name in the schema of the
# Canary tax agency (ATC)
ATC_KEY_MAP = {
    "DetalleIVA": "DetalleIGIC",
    "DesgloseIVA": "DesgloseIGIC",
    "ImporteTransmisionInmueblesSujetoAIVA": "ImporteTransmisionInmueblesSujetoAIGIC",
    # Not subject operations: article 9 of Law 20/1991 instead of 7 and 14 LIVA
    "ImportePorArticulos7_14_Otros": "ImportePorArticulos9_Otros",
    # The IGIC surcharge is the one of the retail traders on their imports
    "CuotaRecargoEquivalencia": "CuotaRecargoMinorista",
}
# Keys of the AEAT SII dictionary that the ATC schema does not have: the retail
# surcharge is only reported by its amount
ATC_DROP_KEYS = {"TipoRecargoEquivalencia"}


class AccountMove(models.Model):
    _inherit = "account.move"

    def _is_atc_sii_agency(self):
        """Whether the document is reported to the SII of the Canary tax agency."""
        self.ensure_one()
        return self._get_sii_tax_agency() == self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias"
        )

    # Do some changes for Canary tax agency
    def _get_aeat_header(self, tipo_comunicacion=False, cancellation=False):
        header = super()._get_aeat_header(
            tipo_comunicacion=tipo_comunicacion, cancellation=cancellation
        )
        if self._is_atc_sii_agency():
            header["IDVersionSii"] = "1.0"
        return header

    @api.model
    def _sii_atc_replace_tax_keys(self, invoice_dic):
        """Recursively rename the keys of the AEAT SII dictionary to the ones of
        the ATC schema, and remove the ones it does not have. Only exact key
        matches are replaced."""
        if isinstance(invoice_dic, dict):
            return {
                ATC_KEY_MAP.get(key, key): self._sii_atc_replace_tax_keys(value)
                for key, value in invoice_dic.items()
                if key not in ATC_DROP_KEYS
            }
        if isinstance(invoice_dic, list):
            return [self._sii_atc_replace_tax_keys(item) for item in invoice_dic]
        if isinstance(invoice_dic, tuple):
            return tuple(self._sii_atc_replace_tax_keys(item) for item in invoice_dic)
        return invoice_dic

    def _get_aeat_invoice_dict_out(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_out(cancel=cancel)
        if self._is_atc_sii_agency():
            inv_dict = self._sii_atc_replace_tax_keys(inv_dict)
        return inv_dict

    def _get_aeat_invoice_dict_in(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_in(cancel=cancel)
        if self._is_atc_sii_agency():
            inv_dict = self._sii_atc_replace_tax_keys(inv_dict)
        return inv_dict

    def _get_aeat_invoice_dict(self):
        inv_dict = super()._get_aeat_invoice_dict()
        # The renamed keys are not in the rounding of l10n_es_aeat_sii_oca
        round_by_keys(inv_dict, ["CuotaRecargoMinorista"])
        return inv_dict

    def _is_sii_reported_tax(self, tax):
        """The SII of the Canary tax agency is for the IGIC: it gets the IGIC
        taxes and the withholdings, not the VAT ones."""
        if self._is_atc_sii_agency():
            return tax.l10n_es_applicability == "03" or (
                not tax.l10n_es_applicability and tax.l10n_es_type == "retencion"
            )
        return super()._is_sii_reported_tax(tax)

    def _get_sii_identifier(self):
        invoice = self
        if self._is_atc_sii_agency():
            invoice = self.with_context(is_canary_tax_agency=True)
        return super(AccountMove, invoice)._get_sii_identifier()
