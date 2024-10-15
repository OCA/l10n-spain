# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class IrCronTrigger(models.Model):
    _inherit = "ir.cron.trigger"

    def do_now(self):
        documents = self.env["account.move"].search(
            [("invoice_cron_trigger_ids", "in", self.ids)]
        )
        documents.write({"sii_send_date": fields.Datetime.now()})
        self.sudo().write({"call_at": fields.Datetime.now()})

    def cancel_now(self):
        documents = self.env["account.move"].search(
            [("invoice_cron_trigger_ids", "in", self.ids)]
        )
        documents.write({"sii_send_date": False})
        self.sudo().unlink()

    def reschedule_sudo(self):
        documents = self.env["account.move"].search(
            [("invoice_cron_trigger_ids", "in", self.ids)]
        )
        for document in documents:
            document.write(
                {"sii_send_date": document.company_id._get_sii_sending_time()}
            )
