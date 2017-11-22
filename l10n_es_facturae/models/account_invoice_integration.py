# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import models, api, fields, exceptions, _


class AccountInvoiceIntegration(models.Model):
    _name = "account.invoice.integration"

    name = fields.Char(default='/', readonly=True)

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        required=True,
        readonly=True
    )

    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('cancelled', 'Cancelled'),
            ('failed', 'Failed'),
        ], default='pending', readonly=True
    )

    attachment_id = fields.Many2one(
        comodel_name='ir.attachment',
        string="Main file"
    )

    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string="Annexes"
    )

    method_id = fields.Many2one(
        comodel_name='account.invoice.integration.method',
        required=True,
        string="Method", readonly=True
    )

    log_ids = fields.One2many(
        comodel_name='account.invoice.integration.log',
        inverse_name='integration_id'
    )

    can_update = fields.Boolean(default=False, readonly=True)
    can_cancel = fields.Boolean(default=False, readonly=True)
    can_send = fields.Boolean(default=True, readonly=True)

    register_number = fields.Char(readonly=True)
    # To be filled for each method
    integration_status = fields.Selection(selection=[], readonly=True)
    integration_description = fields.Char(readonly=True)
    cancellation_status = fields.Selection(selection=[], readonly=True)
    cancellation_description = fields.Char(readonly=True)
    update_date = fields.Datetime(readonly=True)

    _sql_constraints = [
        ('invoice_method_unique',
         'unique(method_id, invoice_id)',
         'Method must be unique per invoice')
    ]

    @api.model
    def create(self, vals):
        if not vals.get('method_id', False):
            raise exceptions.Warning(_('Method is required'))
        if vals.get('name', '/') == '/':
            method = self.env['account.invoice.integration.method'].browse(
                vals['method_id']
            )
            vals['name'] = method.sequence_id.next_by_id() or '/'
        return super(AccountInvoiceIntegration, self).create(vals)

    @api.multi
    def update_action(self):
        for record in self:
            if not record.can_update:
                raise exceptions.Warning(_('Cannot update'))
        log_obj = self.env['account.invoice.integration.log']
        for record in self:
            log_obj.create(record.update_values()).update()

    def log_values(self):
        return {
            'integration_id': self.id
        }

    def cancel_values(self):
        res = self.log_values()
        res['type'] = 'cancel'
        return res

    def update_values(self):
        res = self.log_values()
        res['type'] = 'update'
        return res

    def send_values(self):
        res = self.log_values()
        res['type'] = 'send'
        return res

    @api.multi
    def send_action(self):
        log_obj = self.env['account.invoice.integration.log']
        for record in self:
            log_obj.create(record.send_values()).send()
