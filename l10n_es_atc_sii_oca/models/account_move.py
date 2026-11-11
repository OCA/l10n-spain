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
# Purchase key of the retail traders' regime, the only one that admits the
# implicit tax burden of a purchase to a retail trader
ATC_RETAIL_PURCHASE_CODE = "15_igic_purchase"
# Share of the IGIC rate that a purchase to a retail trader carries implicitly
ATC_IMPLICIT_TAX_SHARE = 0.7
# Purchase keys whose details only admit the base when they are the only key
# (IPSI/VAT, small businesses, art. 25 of Law 19/1994: error 1325)
ATC_BASE_ONLY_PURCHASE_CODES = {"08", "16", "17"}


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
        # The ATC keys are not in the rounding of l10n_es_aeat_sii_oca
        round_by_keys(inv_dict, ["CuotaRecargoMinorista", "CargaImpositivaImplicita"])
        return inv_dict

    def _is_atc_implicit_tax(self, tax):
        """Purchase to a retail trader whose implicit IGIC can be deducted: the
        tax carries the key 15 of the regime and its rate is the 70 % of the
        IGIC one, as the retail trade purchase taxes of the chart of accounts."""
        return (
            tax.type_tax_use == "purchase"
            and tax.l10n_es_type == "sujeto"
            and tax.l10n_es_regime_code == ATC_RETAIL_PURCHASE_CODE
        )

    def _get_sii_tax_dict(self, tax_line, tax_lines):
        """Received IGIC details as the ATC wants them:

        * Purchase to a retail trader: the nominal rate and the implicit tax
          burden instead of the quota (ATC FAQ 8.2, errors 1350 and 2044).
        * Exempt purchase, and any other one of the regular breakdown whose
          only key is 08, 16 or 17: the base alone, without rate nor quota (ATC
          FAQ 8.3, error 1325). The reverse charge details require both.
        """
        tax_dict = super()._get_sii_tax_dict(tax_line, tax_lines)
        if not self.is_purchase_document() or not self._is_atc_sii_agency():
            return tax_dict
        tax = tax_line["tax"]
        codes = self._get_sii_regime_codes()
        if self._is_atc_implicit_tax(tax):
            tax_dict["TipoImpositivo"] = str(
                round(abs(tax.amount) / ATC_IMPLICIT_TAX_SHARE, 2)
            )
            tax_dict["CargaImpositivaImplicita"] = tax_dict.pop("CuotaSoportada")
        elif tax.l10n_es_type == "exento" or (
            tax.l10n_es_type in ("sujeto", "dua", "no_deducible")
            and len(codes) == 1
            and codes[0] in ATC_BASE_ONLY_PURCHASE_CODES
        ):
            tax_dict.pop("TipoImpositivo")
            tax_dict.pop("CuotaSoportada")
        return tax_dict

    @api.model
    def _merge_tax_dict(self, vat_list, tax_dict, comp_keys, merge_keys):
        """The ATC details of a rate can have different amounts (base alone,
        implicit tax burden, retail surcharge): only details with the same keys
        are merged, summing the amounts they have."""
        if not self._is_atc_sii_agency():
            return super()._merge_tax_dict(vat_list, tax_dict, comp_keys, merge_keys)
        for existing_dict in vat_list:
            if existing_dict.keys() != tax_dict.keys() or any(
                existing_dict[key] != tax_dict[key]
                for key in comp_keys
                if key in tax_dict
            ):
                continue
            for key in (*merge_keys, "CargaImpositivaImplicita"):
                if key in tax_dict:
                    existing_dict[key] += tax_dict[key]
            return True
        return False

    def _get_sii_amount_not_in_total(self, tax_line, codes):
        """The ATC checks the total of a received invoice against the bases and
        quotas, without the implicit tax burden of the purchases to retail
        traders (error 2045)."""
        amount = super()._get_sii_amount_not_in_total(tax_line, codes)
        if (
            self.is_purchase_document()
            and self._is_atc_sii_agency()
            and self._is_atc_implicit_tax(tax_line["tax"])
        ):
            amount += tax_line["amount"]
        return amount

    def _get_sii_in_taxes(self):
        """The ATC only admits a deductible quota on the purchases that can
        deduct it: not with the keys 08, 16 or 17 (errors 1328, 1329 and
        1343), nor with the key 15 of the retail traders unless it is the
        implicit tax burden of a purchase to another one (errors 1330 and
        1333)."""
        taxes_dict, tax_amount, not_in_amount_total = super()._get_sii_in_taxes()
        if self._is_atc_sii_agency():
            codes = set(self._get_sii_regime_codes())
            if codes & ATC_BASE_ONLY_PURCHASE_CODES or (
                "15" in codes
                and not any(
                    self._is_atc_implicit_tax(tax)
                    for tax in self._get_sii_document_taxes()
                )
            ):
                tax_amount = 0.0
        return taxes_dict, tax_amount, not_in_amount_total

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
