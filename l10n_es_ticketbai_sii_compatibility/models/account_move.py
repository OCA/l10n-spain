# Copyright 2023 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sii_state = fields.Selection(selection_add=[("exempt", "Exempt")])

    def _process_invoice_for_sii_send(self):
        sii_invoices = self.env["account.move"]
        for invoice in self:
            if (
                invoice.move_type in ["out_invoice", "out_refund"]
                and invoice.company_id.tbai_enabled
            ):
                invoice.sii_state = "exempt"
                continue
            super(AccountMove, self)._process_invoice_for_sii_send()
        return super(AccountMove, sii_invoices)._process_invoice_for_sii_send()
