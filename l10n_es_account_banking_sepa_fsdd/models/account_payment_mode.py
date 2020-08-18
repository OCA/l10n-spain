# Copyright 2016 Comunitea Servicios Tecnológicos <omar@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PaymentMode(models.Model):

    _inherit = "account.payment.mode"

    charge_financed = fields.Boolean(
        "Financed Charge", help="Adds FSDD prefix to sepa file id"
    )
