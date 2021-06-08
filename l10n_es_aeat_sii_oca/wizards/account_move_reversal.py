# Copyright 2017 Tecnativa - Pedro M. Baeza
# Copyright 2020 Valentin Vinagre <valent.vinagre@sygel.es>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    def _default_sii_refund_type_required(self):
        invoices = self.env["account.move"].browse(
            self.env.context.get("active_ids"),
        )
        # If any of the invoices part of the active_ids match the criteria,
        # show the field
        return bool(
            invoices.filtered(
                lambda i: i.move_type in ("in_invoice", "out_invoice")
                and i.company_id.sii_enabled
            )
        )

    def _default_supplier_invoice_number_refund_required(self):
        invoices = (
            self.env["account.move"]
            .browse(
                self.env.context.get("active_ids"),
            )
            .filtered(lambda x: x.move_type == "in_invoice")
        )
        return any(invoices.mapped("company_id.sii_enabled"))

    def _selection_sii_refund_type(self):
        return self.env["account.move"].fields_get(allfields=["sii_refund_type"])[
            "sii_refund_type"
        ]["selection"]

    sii_refund_type_required = fields.Boolean(
        string="Is SII Refund Type required?",
        default=_default_sii_refund_type_required,
    )
    sii_refund_type = fields.Selection(
        selection=_selection_sii_refund_type,
        string="SII Refund Type",
    )

    supplier_invoice_number_refund_required = fields.Boolean(
        string="Is Supplier Invoice Number Required?",
        default=_default_supplier_invoice_number_refund_required,
    )
    supplier_invoice_number_refund = fields.Char(
        string="Supplier Invoice Number",
    )

    def reverse_moves(self):
        obj = self.with_context(
            sii_refund_type=self.sii_refund_type,
            supplier_invoice_number=self.supplier_invoice_number_refund,
        )
        return super(AccountMoveReversal, obj).reverse_moves()
