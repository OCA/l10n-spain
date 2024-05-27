# Copyright 2017 Tecnativa - Pedro M. Baeza
# Copyright 2020 Valentin Vinagre <valent.vinagre@sygel.es>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    def _selection_sii_refund_type(self):
        return self.env["account.move"].fields_get(allfields=["sii_refund_type"])[
            "sii_refund_type"
        ]["selection"]

    sii_refund_type_required = fields.Boolean(
        string="Is SII Refund Type required?",
    )
    sii_refund_type = fields.Selection(
        selection=_selection_sii_refund_type,
        string="SII Refund Type",
    )

    supplier_invoice_number_refund_required = fields.Boolean(
        string="Is Supplier Invoice Number Required?",
    )
    supplier_invoice_number_refund = fields.Char(
        string="Supplier Invoice Number",
    )

    def default_get(self, fields_list):
        """
        The previous default methods have been moved here to avoid computing
        the same queries multiple times, also to avoid duplicated code.
        """
        defaults = super().default_get(fields_list)
        if (
            "sii_refund_type" in fields_list
            or "sii_refund_type_required" in fields_list
        ) and self.env.context.get("active_model") == "account.move":
            invoices = self.env["account.move"].browse(
                self.env.context.get("active_ids"),
            )
            to_refund = invoices.filtered(
                lambda i: i.move_type in ("in_invoice", "out_invoice")
            )
            if any(to_refund.mapped("company_id.sii_enabled")):
                defaults["sii_refund_type"] = "I"
                defaults["sii_refund_type_required"] = True
            supplier_invoices = to_refund.filtered(
                lambda x: x.move_type == "in_invoice"
            )
            if supplier_invoices:
                defaults["supplier_invoice_number_refund_required"] = any(
                    supplier_invoices.mapped("company_id.sii_enabled")
                )
        return defaults

    def reverse_moves(self):
        obj = self.with_context(
            sii_refund_type=self.sii_refund_type,
            supplier_invoice_number=self.supplier_invoice_number_refund,
        )
        return super(AccountMoveReversal, obj).reverse_moves()
