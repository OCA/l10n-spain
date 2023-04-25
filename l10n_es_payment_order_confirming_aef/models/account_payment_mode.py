# Copyright 2023 Tecnativa - Ernesto García Medina
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    aef_confirming_type = fields.Selection(
        string="Tipo de pago",
        default="T",
        selection=[
            ("T", "Transferencia"),
            ("C", "Cheque"),
        ],
    )
    aef_confirming_contract = fields.Char(
        string="Contrato AEF Confirming \
        (13 o 15 dígitos)"
    )
