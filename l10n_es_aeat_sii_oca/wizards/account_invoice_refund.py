# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza

from openerp import api, fields, models


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    def _default_sii_refund_type_required(self):
        invoices = self.env['account.invoice'].browse(
            self.env.context.get('active_ids'),
        )
        return any(invoices.mapped('company_id.sii_enabled'))

    def _selection_sii_refund_type(self):
        return self.env['account.invoice'].fields_get(
            allfields=['sii_refund_type']
        )['sii_refund_type']['selection']

    sii_refund_type_required = fields.Boolean(
        string="Is SII Refund Type required?",
        default=_default_sii_refund_type_required,
    )
    sii_refund_type = fields.Selection(
        selection=_selection_sii_refund_type, string="SII Refund Type",
    )

    @api.multi
    def compute_refund(self, mode='refund'):
        obj = self.with_context(sii_refund_type=self.sii_refund_type)
        return super(AccountInvoiceRefund, obj).compute_refund(mode)
