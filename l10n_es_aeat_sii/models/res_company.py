# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from osv import osv, fields
import exceptions
from tools.translate import _


class ResCompany(osv.osv):
    _inherit = 'res.company'

    _columns = {
        'sii_enabled': fields.boolean(string='Enable SII'),
        'sii_test': fields.boolean(string='Test Enviroment'),
        'sii_method': fields.selection(
            string='Method',
            selection=[('auto', 'Automatic'),('manual', 'Manual')],
            help='By default the invoice send in validate process, with manual '
            'method, there a button to send the invoice.'),
        'use_connector': fields.boolean(
            string='Use connector',
            help='Check it to use connector instead to send the invoice '
                 'when it is validated', readonly=True),
        'chart_template_id': fields.many2one('account.chart.template', 'Chart Template',
            required=True)
    }

    _defaults = {
        'sii_method': 'auto',
    }

ResCompany()

