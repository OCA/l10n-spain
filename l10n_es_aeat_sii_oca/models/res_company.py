# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Studio73 - Pablo Fuentes <pablo@studio73.es>
# Copyright 2017 Studio73 - Jordi Tolsà <jordi@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta
from openerp import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    sii_enabled = fields.Boolean(string='Enable SII')
    sii_test = fields.Boolean(string='Is Test Environment?')
    sii_description_method = fields.Selection(
        string='SII Description Method',
        selection=[('auto', 'Automatic'), ('fixed', 'Fixed'),
                   ('manual', 'Manual')],
        default='manual',
        help="Method for the SII invoices description, can be one of these:\n"
             "- Automatic: the description will be the join of the invoice "
             "  lines description\n"
             "- Fixed: the description write on the below field 'SII "
             "  Description'\n"
             "- Manual (by default): It will be necessary to manually enter "
             "  the description on each invoice\n\n"
             "For all the options you can append a header text using the "
             "below fields 'SII Sale header' and 'SII Purchase header'")
    sii_description = fields.Char(
        string="SII Description",
        help="The description for invoices. Only when the filed SII "
             "Description Method is 'fixed'.")
    sii_header_customer = fields.Char(
        string="SII Customer header",
        help="An optional header description for customer invoices. "
             "Applied on all the SII description methods")
    sii_header_supplier = fields.Char(
        string="SII Supplier header",
        help="An optional header description for supplier invoices. "
             "Applied on all the SII description methods")
    chart_template_id = fields.Many2one(
        comodel_name='account.chart.template', string='Chart Template')
    sii_method = fields.Selection(
        string='Method',
        selection=[('auto', 'Automatic'), ('manual', 'Manual')],
        default='auto',
        help="By default, the invoice is sent/queued in validation process. "
             "With manual method, there's a button to send the invoice.")
    use_connector = fields.Boolean(
        string='Use connector',
        help="Check it to use connector instead of sending the invoice "
             "directly when it's validated")
    send_mode = fields.Selection(
        string="Send mode",
        selection=[
            ('auto', 'On validate'),
            ('fixed', 'At fixed time'),
            ('delayed', 'With delay'),
        ], default='auto',
    )
    sent_time = fields.Float(string="Sent time")
    delay_time = fields.Float(string="Delay time")

    def _get_sii_eta(self):
        if self.send_mode == 'fixed':
            now = datetime.now()
            hour, minute = divmod(self.sent_time, 1)
            hour = int(hour)
            minute = int(minute * 60)
            if now.date > hour or (now.hour == hour and now.minute > minute):
                now += timedelta(days=1)
            return now.replace(hour=hour, minute=minute)
        elif self.send_mode == 'delayed':
            return datetime.now() + timedelta(seconds=self.delay_time * 3600)
        else:
            return None
