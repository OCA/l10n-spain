# Copyright 2016 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PaymentMode(models.Model):
    _inherit = "account.payment.mode"

    facturae_code = fields.Selection(
        selection=[
            ("01", "[01] Al contado"),
            ("02", "[02] Recibo Domiciliado"),
            ("03", "[03] Recibo"),
            ("04", "[04] Transferencia"),
            ("05", "[05] Letra Aceptada"),
            ("06", "[06] Crédito Documentario"),
            ("07", "[07] Contrato Adjudicación"),
            ("08", "[08] Letra de cambio"),
            ("09", "[09] Pagaré a la Orden"),
            ("10", "[10] Pagaré No a la Orden"),
            ("11", "[11] Cheque"),
            ("12", "[12] Reposición"),
            ("13", "[13] Especiales"),
            ("14", "[14] Compensación"),
            ("15", "[15] Giro postal"),
            ("16", "[16] Cheque conformado"),
            ("17", "[17] Cheque bancario"),
            ("18", "[18] Pago contra reembolso"),
            ("19", "[19] Pago mediante tarjeta"),
        ],
        default="04",
    )
