# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import models, fields


class AccountInvoiceIntegration(models.Model):
    _inherit = "account.invoice.integration"

    integration_status = fields.Selection(selection_add=[
        ('efact-SENT', 'Sended'),
        ('efact-DELIVERED', 'Delivered'),
        ('efact-REGISTERED', 'Registered'),
        ('efact-ACCEPTED', 'Accepted'),
        ('efact-PAID', 'Paid'),
        ('efact-REJECTED', 'Rejected'),
    ])
    method_code = fields.Char(related='method_id.code', readonly=True)
    efact_hub_id = fields.Char(index=True, readonly=True)
    efact_reference = fields.Char(index=True, readonly=True)
