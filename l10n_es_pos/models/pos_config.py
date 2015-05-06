# -*- coding: utf-8 -*-
# See README.rst file on addon root folder for license details

from openerp import models, fields
from openerp.addons import decimal_precision as dp


class PosConfig(models.Model):
    _inherit = 'pos.config'

    simplified_invoice_limit = fields.Float(
        string='Simplified invoice limit', digits=dp.get_precision('Account'),
        help='Over this amount is not legally posible to create a '
             'simplified invoice',
        default=3000)
