# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import models, fields


class AccountInvoiceIntegration(models.Model):
    _inherit = "account.invoice.integration"

    integration_status = fields.Selection(selection_add=[
        ('face-1200', 'Registered on REC'),
        ('face-1300', 'Registered on RCF'),
        ('face-2400', 'Accepted'),
        ('face-2500', 'Payed'),
        ('face-2600', 'Rejected'),
        ('face-3100', 'Cancellation approved'),
    ])
    cancellation_status = fields.Selection(selection_add=[
        ('face-4100', 'Not requested'),
        ('face-4200', 'Cancellation requested'),
        ('face-4300', 'Cancellation accepted'),
        ('face-4400', 'Cancellation rejected'),
    ])
