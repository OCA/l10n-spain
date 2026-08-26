# © 2017 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# © 2018 FactorLibre - Victor Rodrigo <victor.rodrigo@factorlibre.com>
# © 2022 ProcessControl - David Ramia <david.ramia@processcontrol.es>
# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_invoice_summary = fields.Boolean("Is SII simplified invoice Summary?")
    sii_invoice_summary_start = fields.Char("SII Invoice Summary: First Invoice")
    sii_invoice_summary_end = fields.Char("SII Invoice Summary: Last Invoice")

    def _is_aeat_summary_invoice(self):
        if (
            self.is_invoice_summary
            and self.is_sale_document()
            and self.sii_invoice_summary_start != self.sii_invoice_summary_end
        ):
            return True
        return False

    def _is_aeat_unidentified_document(self):
        # En el SII, una factura resumen (F4) debe considerarse, a efectos de estructura
        # y validaciones, equivalente a una factura simplificada (F2), compartiendo
        # todas sus restricciones y campos obligatorios, con la única diferencia de
        # requerir la clave TipoFactura = F4 y el campo adicional
        # NumSerieFacturaEmisorResumenFin
        return self.is_invoice_summary or super()._is_aeat_unidentified_document()

    def _get_sii_invoice_type(self):
        invoice_type = super()._get_sii_invoice_type()
        if self._is_aeat_summary_invoice() and invoice_type == "F2":
            invoice_type = "F4"
        return invoice_type

    def _get_aeat_invoice_dict_out(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_out(cancel=cancel)
        if inv_dict.get("FacturaExpedida", {}).get("TipoFactura", "") == "F4":
            inv_dict["IDFactura"][
                "NumSerieFacturaEmisor"
            ] = self.sii_invoice_summary_start
            inv_dict["IDFactura"][
                "NumSerieFacturaEmisorResumenFin"
            ] = self.sii_invoice_summary_end
        return inv_dict

    def write(self, vals):
        """Cannot let change sii_invoice_summary fields
        values in a SII registered supplier invoice"""
        for invoice in self.filtered(
            lambda x: x.is_invoice_summary and x.aeat_state != "not_sent"
        ):
            if "sii_invoice_summary_start" in vals:
                invoice._raise_exception_sii(_("SII Invoice Summary: First Invoice"))
            if "sii_invoice_summary_end" in vals:
                invoice._raise_exception_sii(_("SII Invoice Summary: Last Invoice"))
        return super().write(vals)
