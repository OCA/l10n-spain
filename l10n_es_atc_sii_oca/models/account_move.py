# Copyright 2025 Sistema de datos - Mario Montes
# Copyright 2025 Tecnativa - Sergio Teruel
import logging

from odoo import models

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

    def _get_aeat_invoice_dict_out(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_out(cancel=cancel)
        if self._get_sii_tax_agency() == self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias"
        ):
            inv_dict["DetalleIVA"] = inv_dict.pop("DetalleIVA", ["DetalleIGIC"])
            inv_dict["DesgloseIVA"] = inv_dict.pop("DesgloseIVA", ["DetalleIGIC"])
            inv_dict["ImporteTransmisionInmueblesSujetoAIVA"] = inv_dict.pop(
                "ImporteTransmisionInmueblesSujetoAIVA",
                ["ImporteTransmisionInmueblesSujetoAIGIC"],
            )
            inv_dict["PeriodoImpositivo"] = inv_dict.pop(
                "PeriodoImpositivo", ["DetalleIGIC"]
            )
        return inv_dict

    def _get_sii_invoice_dict_in(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_in(cancel=cancel)
        if self._get_sii_tax_agency() == self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias"
        ):
            if self.sii_registration_key.code == "15":
                for p in inv_dict["FacturaRecibida"]["DesgloseFactura"]["DesgloseIGIC"][
                    "DetalleIGIC"
                ]:
                    p.pop("CuotaSoportada")
        return inv_dict
