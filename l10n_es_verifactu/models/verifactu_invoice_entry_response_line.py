# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

VERIFACTU_SEND_STATES = [
    ("not_sent", "Not sent"),
    ("correct", "Sent and Correct"),
    ("incorrect", "Sent and Incorrect"),
    ("accepted_with_errors", "Sent and accepted with errors"),
]


class VerifactuInvoiceEntryResponseLine(models.Model):
    _name = "verifactu.invoice.entry.response.line"
    _description = "Verifactu Send Log"
    _order = "id desc"

    entry_id = fields.Many2one("verifactu.invoice.entry")
    entry_response_id = fields.Many2one("verifactu.invoice.entry.response")
    model = fields.Char(readonly=True)
    document_id = fields.Many2oneReference(
        string="Document",
        model_field="model",
        readonly=True,
        index=True,
    )
    response = fields.Text()
    send_state = fields.Selection(
        selection=VERIFACTU_SEND_STATES,
        string="Verifactu send state",
        default="not_sent",
        readonly=True,
        copy=False,
        help="Indicates the state of this document in relation with the "
        "presentation to Verifactu.",
    )
    verifactu_csv = fields.Text(related="entry_response_id.verifactu_csv")
    error_code = fields.Char()
