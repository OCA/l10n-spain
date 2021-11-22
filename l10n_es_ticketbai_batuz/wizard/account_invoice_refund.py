# Copyright 2021 Digital5, S.L.

from odoo import api, fields, models


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    def _default_batuz_supplier_invoice_number_required(self):
        invoices = self.env["account.invoice"].browse(
            self.env.context.get("active_ids"),
        ).filtered(lambda x: x.type == "in_invoice")
        return any(invoices.mapped("company_id.tbai_enabled"))

    batuz_supplier_invoice_number_required = fields.Boolean(
        string="Is Supplier Invoice Number Required?",
        default=_default_batuz_supplier_invoice_number_required,
    )
    batuz_supplier_invoice_number = fields.Char(
        string="Supplier Invoice Number",
    )

    @api.multi
    def compute_refund(self, mode="refund"):
        wizard = self.with_context(
            batuz_supplier_invoice_number=self.batuz_supplier_invoice_number)
        return super(AccountInvoiceRefund, wizard).compute_refund(mode)
