# Copyright 2025 Sistema de datos - Mario Montes
# Copyright 2025 Tecnativa - Sergio Teruel
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    # Do some changes for Canary tax agency
    def _get_aeat_header(self, tipo_comunicacion=False, cancellation=False):
        header = super()._get_aeat_header(
            tipo_comunicacion=tipo_comunicacion, cancellation=cancellation
        )
        if self._get_sii_tax_agency() == self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias"
        ):
            header["IDVersionSii"] = "1.0"
        return header

    @api.model
    def _sii_atc_replace_tax_keys(self, invoice_dic):
        """
        Recursively replace specific tax-related keys in a nested structure.
        Only exact key matches are replaced.
        """

        key_map = {
            "DetalleIVA": "DetalleIGIC",
            "DesgloseIVA": "DesgloseIGIC",
            "ImporteTransmisionInmueblesSujetoAIVA": (
                "ImporteTransmisionInmueblesSujetoAIGIC"
            ),
        }
        if isinstance(invoice_dic, dict):
            new_dict = {}
            for key, value in invoice_dic.items():
                new_key = key_map.get(key, key)
                new_dict[new_key] = self._sii_atc_replace_tax_keys(value)
            return new_dict
        if isinstance(invoice_dic, list):
            return [self._sii_atc_replace_tax_keys(item) for item in invoice_dic]
        if isinstance(invoice_dic, tuple):
            return tuple(self._sii_atc_replace_tax_keys(item) for item in invoice_dic)
        return invoice_dic

    def _get_aeat_invoice_dict_out(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_out(cancel=cancel)
        if self._get_sii_tax_agency() == self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias"
        ):
            inv_dict = self._sii_atc_replace_tax_keys(inv_dict)
        return inv_dict

    def _get_aeat_invoice_dict_in(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_in(cancel=cancel)
        if self._get_sii_tax_agency() == self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias"
        ):
            inv_dict = self._sii_atc_replace_tax_keys(inv_dict)
        return inv_dict
