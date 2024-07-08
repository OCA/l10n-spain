# © 2019 FactorLibre - Daniel Duque <daniel.duque@factorlibre.com>
# © 2024 FactorLibre - Alejandro Ji Cheung <alejandro.jicheung@factorlibre.com>
# © 2024 FactorLibre - Aritz Olea <aritz.olea@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sii_force_communication_type = fields.Selection(
        string="Force communication type",
        compute="_compute_sii_force_communication_type",
        store=True,
        readonly=False,
        selection=[
            ("A0", "[A0] Alta de facturas/registro"),
            ("A1", "[A1] Modificación de facturas/registros (errores registrales)"),
            ("A4", "[A4] Modificación Factura Régimen de Viajeros"),
            ("A5", "[A5] Alta de las devoluciones del IVA de viajeros"),
            ("A6", "[A6] Modificación de las devoluciones del IVA de viajeros"),
        ],
    )

    sii_allow_force_communication_type = fields.Boolean(
        "Allow force communication type on invoices",
        related="fiscal_position_id.sii_allow_force_communication_type",
    )

    @api.depends("fiscal_position_id", "sii_allow_force_communication_type")
    def _compute_sii_force_communication_type(self):
        for invoice in self.filtered("fiscal_position_id"):
            if invoice.sii_allow_force_communication_type:
                invoice.sii_force_communication_type = (
                    invoice.fiscal_position_id.sii_forced_communication_type
                )

    def _get_sii_header(self, tipo_comunicacion=False, cancellation=False):
        header = super()._get_sii_header(tipo_comunicacion, cancellation)
        if (
            self.sii_allow_force_communication_type
            and self.sii_force_communication_type
        ):
            header.update({"TipoComunicacion": self.sii_force_communication_type})
        return header
