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

    def _default_supplier_invoice_number_refund_required(self):
        invoices = self.env['account.invoice'].browse(
            self.env.context.get('active_ids'),
        ).filtered(lambda x: x.type == 'in_invoice')

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

    supplier_invoice_number_refund_required = fields.Boolean(
        string="Is Supplier Invoice Number Required?",
        default=_default_supplier_invoice_number_refund_required,
    )
    supplier_invoice_number_refund = fields.Char(
        string="Supplier Invoice Number",
    )

    @api.onchange('filter_refund')
    def onchange_filter_refund(self):
        if not self.sii_refund_type_required:
            return
        self.sii_refund_type = 'S' if self.filter_refund == 'modify' else 'I'

    @api.multi
    def compute_refund(self, mode='refund'):
        obj = self.with_context(
            sii_refund_type=self.sii_refund_type,
            supplier_invoice_number=self.supplier_invoice_number_refund,
        )
        result = super(AccountInvoiceRefund, obj).compute_refund(mode)
        if mode not in ['modify']:
            return result
        created_inv_ids = [t[2] for t in result['domain'] if t[0] == 'id'][0]
        for invoice in self.env['account.invoice'].browse(created_inv_ids):
            if invoice.type not in ['out_invoice', 'in_invoice']:
                continue
            invoice.sii_substitution_refund = True
        return result
