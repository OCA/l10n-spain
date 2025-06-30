# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

VERIFACTU_SEND_STATES = [
    ("not_sent", "Not sent"),
    ("correct", "Sent and Correct"),
    ("incorrect", "Sent and Incorrect"),
    ("accepted_with_errors", "Sent and accepted with errors"),
]


class VerifactuSendResponseLine(models.Model):
    _name = "verifactu.send.response.line"
    _description = "Verifactu Send Log"
    _order = "id desc"

    send_queue_id = fields.Many2one("verifactu.send.queue")
    send_response_id = fields.Many2one("verifactu.send.response")
    move_id = fields.Many2one(related="send_queue_id.move_id")
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
    verifactu_csv = fields.Text(related="send_response_id.verifactu_csv")
    error_code = fields.Char()
