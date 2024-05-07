import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = ["account.move"]

    def _get_sii_header(self, tipo_comunicacion=False, cancellation=False):
        header = super()._get_sii_header(tipo_comunicacion, cancellation)
        header["IDVersionSii"] = "1.0"
        return header

    def _get_sii_invoice_dict(self):
        inv_dict = super()._get_sii_invoice_dict()
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
        inv_dict = super()._get_sii_invoice_dict_in(cancel)
        if self.sii_registration_key.code == "15":
            for p in inv_dict["FacturaRecibida"]["DesgloseFactura"]["DesgloseIGIC"][
                "DetalleIGIC"
            ]:
                p.pop("CuotaSoportada")
        return inv_dict
