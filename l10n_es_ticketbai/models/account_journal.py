#  Copyright 2021 Landoo Sistemas de Informacion SL
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    tbai_enabled = fields.Boolean(related="company_id.tbai_enabled", readonly=True)

    tbai_send_invoice = fields.Boolean(
        string="Send TicketBAI invoices to tax agency", default=True
    )

    @api.onchange("refund_sequence")
    def onchange_refund_sequence(self):
        if not self.refund_sequence and self.type == "sale":
            self.refund_sequence = True

    @api.onchange("type")
    def onchange_type(self):
        if self.type == "sale":
            self.refund_sequence = True

    @api.onchange("tbai_send_invoice")
    def onchange_tbai_send_invoice(self):
        if not self.tbai_send_invoice:
            tbai_invoices = self.env["account.move"].search(
                [("journal_id", "=", self._origin.id), ("tbai_invoice_id", "!=", False)]
            )
            if len(tbai_invoices) > 0:
                raise UserError(
                    _(
                        "You cannot stop sending invoices from this"
                        " journal, an invoice has already been sent."
                    )
                )
