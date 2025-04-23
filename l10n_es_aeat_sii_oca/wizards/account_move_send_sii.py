# Copyright 2023 Pol Reig <pol.reig@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SendSIIWizard(models.TransientModel):
    _name = "wizard.send.sii"
    _description = "Send SII Wizard"

    moves_to_send = fields.Integer()
    not_send_without_errors_number = fields.Integer()
    with_errors_number = fields.Integer()
    modified_number = fields.Integer()
    account_move_ids = fields.Many2many("account.move", string="Invoices")

    def default_get(self, fields):
        res = super().default_get(fields)
        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids", [])
        account_moves = self.env[active_model].browse(active_ids)
        not_send_without_errors = account_moves.filtered(
            lambda a: a.aeat_state == "not_sent" and not a.aeat_send_failed
        )
        with_errors = account_moves.filtered(lambda a: a.aeat_send_failed)
        modified = account_moves.filtered(
            lambda a: a.aeat_state in ["sent_modified", "cancelled_modified"]
        )
        moves_to_send = account_moves.filtered(
            lambda a: a.sii_enabled
            and a.state in a._get_valid_document_states()
            and a.aeat_state not in ["sent", "cancelled"]
        )
        res.update(
            {
                "moves_to_send": len(moves_to_send),
                "account_move_ids": moves_to_send.ids,
                "not_send_without_errors_number": len(not_send_without_errors),
                "with_errors_number": len(with_errors),
                "modified_number": len(modified),
            }
        )
        return res

    def action_confirm(self):
        self.account_move_ids.send_sii()
