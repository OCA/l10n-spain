# Copyright 2023 Tecnativa - Ernesto García Medina
# Copyright 2024 Tecnativa - Víctor Martínez
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
    aef_confirming_modality = fields.Selection(
        string="Modalidad remesa",
        default=False,
        selection=[
            ("1", "Estandar"),
            ("2", "Pronto pago"),
            ("3", "Otros"),
        ],
        help="Opcional: Consultar con la entidad bancaria",
    )
    aef_confirming_contract = fields.Char(
        string="Contrato AEF Confirming \
        (13 o 15 dígitos)"
    )
