# Copyright 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveReversal(models.TransientModel):
    """Refunds move"""

    _inherit = "account.move.reversal"

    correction_method = fields.Selection(
        selection=[
            ("01", "Rectificación íntegra"),
            ("02", "Rectificación por diferencias"),
            (
                "03",
                "Rectificación por descuento por volumen de operaciones "
                "durante un periodo",
            ),
            ("04", "Autorizadas por la Agencia Tributaria"),
        ],
        default="02",
    )

    refund_reason = fields.Selection(
        selection=[
            ("01", "Número de la factura"),
            ("02", "Serie de la factura"),
            ("03", "Fecha expedición"),
            ("04", "Nombre y apellidos/Razón social - Emisor"),
            ("05", "Nombre y apellidos/Razón social - Receptor"),
            ("06", "Identificación fiscal Emisor/Obligado"),
            ("07", "Identificación fiscal Receptor"),
            ("08", "Domicilio Emisor/Obligado"),
            ("09", "Domicilio Receptor"),
            ("10", "Detalle Operación"),
            ("11", "Porcentaje impositivo a aplicar"),
            ("12", "Cuota tributaria a aplicar"),
            ("13", "Fecha/Periodo a aplicar"),
            ("14", "Clase de factura"),
            ("15", "Literales legales"),
            ("16", "Base imponible"),
            ("80", "Cálculo de cuotas repercutidas"),
            ("81", "Cálculo de cuotas retenidas"),
            ("82", "Base imponible modificada por devolución de envases" "/embalajes"),
            ("83", "Base imponible modificada por descuentos y " "bonificaciones"),
            (
                "84",
                "Base imponible modificada por resolución firme, judicial "
                "o administrativa",
            ),
            (
                "85",
                "Base imponible modificada cuotas repercutidas no "
                "satisfechas. Auto de declaración de concurso",
            ),
        ],
        default="10",
    )

    def _prepare_default_reversal(self, move):
        values = super()._prepare_default_reversal(move)
        for key in ("correction_method", "facturae_refund_reason"):
            if self.env.context.get(key):
                values[key] = self.env.context[key]
        return values

    def reverse_moves(self):
        """Inject in the context the Facturae refund values for being later
        added to the dictionary values for creating the refund.
        """
        return super(
            AccountMoveReversal,
            self.with_context(
                correction_method=self.correction_method,
                facturae_refund_reason=self.refund_reason,
            ),
        ).reverse_moves()
