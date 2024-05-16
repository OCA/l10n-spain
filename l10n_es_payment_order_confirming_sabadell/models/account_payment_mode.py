# Copyright 2016 Soluntec Proyectos y Soluciones TIC. - Rubén Francés
# Copyright 2016 Soluntec Proyectos y Soluciones TIC. - Nacho Torró
# Copyright 2015 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    conf_sabadell_type = fields.Selection(
        string="Tipo de pago",
        default="56",
        selection=[
            ("56", "Tranferencia"),
            ("57", "Cheque"),
            ("58", "Transferencia al extranjero"),
        ],
    )
    tipo_envio_info = fields.Selection(
        string="Tipo envío información",
        default="1",
        selection=[("1", "Correo"), ("2", "Fax"), ("3", "Email")],
    )
    contrato_bsconfirming = fields.Char(
        string="Contrato BSConfirming \
        (12 dígitos)"
    )
    codigo_estadistico = fields.Char(
        string="Codigo Estadístico para \
        Transferencia Internacional (6 caracteres)",
        default="000000",
    )
