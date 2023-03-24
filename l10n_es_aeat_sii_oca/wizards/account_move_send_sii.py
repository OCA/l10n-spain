# Copyright 2023 Pol Reig <pol.reig@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SendSIIWizard(models.TransientModel):
    _name = "wizard.send.sii"
    _description = "Send SII Wizard"

    sending_number = fields.Integer(string="Invoices Jobs Process Sending")
    sent_number = fields.Integer(string="Invoices SII Sent")
    account_move_ids = fields.Many2many("account.move", string="Invoices")

    def default_get(self, fields):
        res = super().default_get(fields)
        # get the records selected
        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids", [])
        account_moves = self.env[active_model].browse(active_ids)
        # filter the records that have jobs associated
        invoices_with_jobs_ids = account_moves.filtered(lambda i: (i.invoice_jobs_ids))
        # and calculate the number of invoices in process of sending or sent
        sending_number = len(invoices_with_jobs_ids)
        sent_number = 0
        for invoice in invoices_with_jobs_ids:
            if all(invoice.invoice_jobs_ids.mapped("state")) == "failed":
                sending_number -= 1
            elif all(invoice.invoice_jobs_ids.mapped("state")) == "cancelled":
                sending_number -= 1
            elif any(invoice.invoice_jobs_ids.mapped("state")) == "done":
                sent_number += 1
        # update the values of the wizard
        res.update(
            {
                "sending_number": sending_number,
                "sent_number": sent_number,
                "account_move_ids": [(6, 0, active_ids)],
            }
        )
        return res

    def action_confirm(self):
        self.account_move_ids.send_sii()
