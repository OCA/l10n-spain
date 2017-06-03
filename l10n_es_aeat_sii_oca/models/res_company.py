# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# (c) 2017 Studio73 - Pablo Fuentes <pablo@studio73.es>
# (c) 2017 Studio73 - Jordi Tolsà <jordi@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta

from openerp import models, fields, api, _
from openerp.exceptions import Warning


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    @api.onchange('use_connector')
    def _check_connector_installed(self):
        module = self.env['ir.module.module'].search(
            [('name', '=', 'connector'), ('state', '=', 'installed')])
        if not module:
            raise Warning(
                _('The module "Connector" is not installed. You have '
                  'to install it to activate this option'))

    sii_enabled = fields.Boolean(string='Enable SII')
    sii_test = fields.Boolean(string='Test Enviroment')
    chart_template_id = fields.Many2one(
        comodel_name='account.chart.template', string='Chart Template')
    use_connector = fields.Boolean(
        string='Use connector',
        help='Check it to use connector instead to send the invoice '
        'when it is validated')

    send_mode = fields.Selection(string="Send mode",
                                 selection=[('auto', 'On validate'),
                                            ('fixed', 'At fixed time'),
                                            ('delayed', 'With delay')],
                                 default='auto')
    sent_time = fields.Float(string="Sent time")
    delay_time = fields.Float(string="Delay time")

    def _get_sii_eta(self):
        if self.send_mode == 'fixed':
            now = datetime.now()

            hour, minute = divmod(self.sent_time, 1)
            hour = int(hour)
            minute = int(minute*60)

            if now.date > hour or (now.hour == hour and now.minute > minute):
                now += timedelta(days=1)

            return now.replace(hour=hour, minute=minute)

        elif self.send_mode == 'delayed':
            return datetime.now() + timedelta(seconds=self.delay_time * 60 * 60)

        else:
            return None
