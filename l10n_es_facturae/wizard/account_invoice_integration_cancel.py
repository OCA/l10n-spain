# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class AccountInvoiceIntegrationCancel(models.TransientModel):
    _name = 'account.invoice.integration.cancel'
    _description = 'Cancels a created integration'

    integration_id = fields.Many2one(
        comodel_name='account.invoice.integration'
    )

    def cancel_values(self):
        return {
            'integration_id': self.integration_id.id,
            'type': 'cancel'
        }

    @api.multi
    def cancel_integration(self):
        self.ensure_one()
        self.env['account.invoice.integration.log'].create(
            self.cancel_values()
        ).cancel()
