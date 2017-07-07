# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.osv import osv, fields


class ResPartner(osv.Model):
    _inherit = 'res.partner'

    _columns = {
        'sii_simplified_invoice': fields.boolean(
            string="Simplified invoices in SII?",
            help="Checking this mark, invoices done to this partner will be "
                 "sent to SII as simplified invoices."
        )
    }
