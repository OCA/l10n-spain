# Copyright 2023 Pol Reig <pol.reig@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SendSIIWizard(models.TransientModel):
    _name = "wizard.send.sii"
    _description = "Send SII Wizard"

    sending_number = fields.Integer()
    not_send_without_errors_number = fields.Integer()
    with_errors_number = fields.Integer()
    modified_number = fields.Integer()
    account_move_ids = fields.Many2many("account.move", string="Invoices")

    def default_get(self, fields):
        res = super().default_get(fields)
        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids", [])
        account_moves = self.env[active_model].browse(active_ids)
        invoices_with_triggers = account_moves.filtered(
            lambda i: (i.invoice_cron_trigger_ids)
        )
        invoices_without_triggers = account_moves - invoices_with_triggers
        not_send_without_errors = invoices_without_triggers.filtered(
            lambda a: a.aeat_state == "not_sent" and not a.sii_send_failed
        )
        with_errors = invoices_without_triggers.filtered(lambda a: a.sii_send_failed)
        modified = invoices_without_triggers.filtered(
            lambda a: a.aeat_state in ["sent_modified", "cancelled_modified"]
        )
        res.update(
            {
                "sending_number": len(invoices_with_triggers),
                "not_send_without_errors_number": len(not_send_without_errors),
                "with_errors_number": len(with_errors),
                "modified_number": len(modified),
            }
        )
        return res

    def action_confirm(self):
        self.account_move_ids.send_sii()
