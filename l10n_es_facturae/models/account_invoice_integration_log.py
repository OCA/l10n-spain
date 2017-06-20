# -*- coding: utf-8 -*-
# © 2017 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields, exceptions, _, api

from datetime import datetime


class AccountInvoiceIntegrationLog(models.Model):
    _name = "account.invoice.integration.log"

    name = fields.Char(default='/', readonly=True)

    integration_id = fields.Many2one(
        comodel_name='account.invoice.integration',
        required=True,
        readonly=True
    )

    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('failed', 'Failed')
        ]
    )

    result_code = fields.Char()

    type = fields.Selection(
        selection=[
            ('send', 'Send'),
            ('update', 'Update'),
            ('cancel', 'Cancel')
        ]
    )

    log = fields.Text()
    update_date = fields.Datetime()
    cancellation_motive = fields.Char()

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'account.invoice.integration.log'
            ) or '/'
        return super(AccountInvoiceIntegrationLog, self).create(vals)

    def update(self):
        if self.integration_id.can_update:
            return self.update_method()
        raise exceptions.ValidationError(_('Integration cannot be update'))

    # To be overwritten
    def update_method(self):
        if self.integration_id.method_id.code == 'demo':
            self.state = 'sent'
            self.update_date = datetime.now()
            return
        raise exceptions.Warning(_('No update method has been created'))

    def cancel(self):
        if self.integration_id.can_update:
            return self.cancel_method()
        raise exceptions.ValidationError(_('Integration cannot be cancelled'))

    # To be overwritten
    def cancel_method(self):
        if self.integration_id.method_id.code == 'demo':
            self.state = 'sent'
            self.integration_id.state = 'cancelled'
            self.integration_id.can_cancel = False
            return
        raise exceptions.Warning(_('No cancel method has been created'))

    def send(self):
        if self.integration_id.can_send:
            return self.send_method()
        raise exceptions.ValidationError(_('Integration cannot be sent'))

    # To be overwritten
    def send_method(self):
        if self.integration_id.method_id.code == 'demo':
            self.state = 'sent'
            self.integration_id.state = 'sent'
            self.integration_id.can_cancel = True
            self.integration_id.can_update = True
            self.integration_id.can_send = False
            self.update_date = datetime.now()
            return
        self.state = 'failed'
        raise exceptions.Warning(_('No sending method has been created'))
