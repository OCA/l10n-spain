# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnológicos <omar@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class PaymentMode(models.Model):

    _inherit = "payment.mode"

    charge_financed = fields.Boolean(
        'Financed Charge', help="Adds FSDD prefix to sepa file id")
