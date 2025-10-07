# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

from ..models.verifactu_invoice_entry import VERIFACTU_SEND_STATES


class VerifactuInvoiceEntryResponseLine(models.Model):
    _name = "verifactu.invoice.entry.response.line"
    _description = "VERI*FACTU send log"
    _order = "id desc"

    entry_id = fields.Many2one(comodel_name="verifactu.invoice.entry", required=True)
    entry_response_id = fields.Many2one("verifactu.invoice.entry.response")
    model = fields.Char(readonly=True)
    document_id = fields.Many2oneReference(
        string="Document", model_field="model", readonly=True, index=True
    )
    response = fields.Text()
    send_state = fields.Selection(
        selection=VERIFACTU_SEND_STATES,
        string="VERI*FACTU send state",
        default="not_sent",
        readonly=True,
        copy=False,
        help="Indicates the state of this document in relation with the "
        "presentation to VERI*FACTU.",
    )
    verifactu_csv = fields.Text(related="entry_response_id.verifactu_csv")
    error_code = fields.Char()
    document_name = fields.Char(related="entry_id.document_name", readonly=True)

    @property
    def document(self):
        return self.env[self.model].browse(self.document_id).exists()
