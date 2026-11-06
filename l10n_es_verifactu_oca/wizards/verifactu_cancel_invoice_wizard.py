# Copyright 2025 Factor Libre - Almudena de La Puente
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class VerifactuCancelInvoiceWizard(models.TransientModel):
    _name = "verifactu.cancel.invoice.wizard"
    _description = "VERI*FACTU cancel invoice wizard"

    invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice",
        required=True,
        readonly=True,
    )
    cancel_reason = fields.Char(string="Cancellation reason")

    def cancel_invoice_in_verifactu(self):
        self.ensure_one()
        invoice = self.invoice_id
        invoice.verifactu_cancel_reason = self.cancel_reason
        res = invoice.with_context(verifactu_cancel=True).button_cancel()
        invoice.cancel_verifactu()
        return res
