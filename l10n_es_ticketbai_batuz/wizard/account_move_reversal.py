# Copyright 2021 Digital5, S.L.
# Copyright 2022 Landoo Sistemas de Informacion SL

from odoo import fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    def _default_batuz_supplier_invoice_number_required(self):
        invoices = (
            self.env["account.move"]
            .browse(
                self.env.context.get("active_ids"),
            )
            .filtered(lambda x: x.move_type == "in_invoice")
        )
        return any(invoices.mapped("company_id.tbai_enabled"))

    batuz_supplier_invoice_number_required = fields.Boolean(
        string="Is Supplier Invoice Number Required?",
        default=_default_batuz_supplier_invoice_number_required,
    )
    batuz_supplier_invoice_number = fields.Char(
        string="Supplier Invoice Number",
    )

    def reverse_moves(self):
        wizard = self.with_context(
            batuz_supplier_invoice_number=self.batuz_supplier_invoice_number
        )
        return super(AccountMoveReversal, wizard).reverse_moves()
