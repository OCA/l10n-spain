# -*- coding: utf-8 -*-
# © 2017 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields


class AccountInvoiceIntegrationMethod(models.Model):
    _name = "account.invoice.integration.method"

    name = fields.Char()
    code = fields.Char(readonly=True)
    sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        readonly=True,
        required=True
    )

    # Default values for integration. It could be extended
    def integration_values(self, invoice):
        return {
            'method_id': self.id,
            'invoice_id': invoice.id
        }

    def create_integration(self, invoice):
        self.ensure_one()
        self.env['account.invoice.integration'].create(
            self.integration_values(invoice)
        )
