# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnológicos <omar@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields


class PaymentMode(orm.Model):

    _inherit = "payment.mode"

    _columns = {
    'charge_financed' : fields.boolean(
        'Financed Charge', help="Adds FSDD prefix to sepa file id")
    }       
