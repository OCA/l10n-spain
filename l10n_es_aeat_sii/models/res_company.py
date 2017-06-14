# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Alberto Martín Cortada <alberto.martin@guadaltech.es>
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.osv import osv, fields
from openerp import exceptions
from openerp.tools.translate import _
from datetime import datetime, timedelta


class ResCompany(osv.Model):
    _inherit = 'res.company'

    _columns = {
        'sii_test': fields.boolean(string='Test Enviroment'),
        'sii_enabled': fields.boolean(string='Enable SII'),
        'chart_template_id': fields.many2one('account.chart.template', 'Chart Template',
                                             required=True),
        'sii_method': fields.selection(
            string='Method',
            selection=[('auto', 'Automatic'), ('manual', 'Manual')],
            help='By default the invoice send in validate process, with manual '
                 'method, there a button to send the invoice.'),
        'send_mode': fields.selection(string="Send mode",
                                      selection=[('auto', 'On validate'),
                                                 ('fixed', 'At fixed time'),
                                                 ('delayed', 'With delay')],
                                      ),
        # 'sent_time': fields.float(string="Sent time"),
        # 'delay_time': fields.float(string="Delay time"),

    }

    _defaults = {
        'send_mode': 'auto',
        'sii_method': 'auto',
    }

    # def _get_sii_eta(self, cr, uid, ids):
    #     for company in self.browse(cr, uid, ids):
    #         if company.send_mode == 'fixed':
    #             now = datetime.now()
    #
    #             hour, minute = divmod(company.sent_time, 1)
    #             hour = int(hour)
    #             minute = int(minute * 60)
    #
    #             if now.date > hour or (now.hour == hour and now.minute > minute):
    #                 now += timedelta(days=1)
    #
    #             return now.replace(hour=hour, minute=minute)
    #
    #         elif company.send_mode == 'delayed':
    #             return datetime.now() + timedelta(seconds=self.delay_time * 60 * 60)
    #
    #         else:
    #             return None
