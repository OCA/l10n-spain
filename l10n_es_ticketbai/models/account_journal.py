#  Copyright 2022 Digital5, S.L.
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    tbai_enabled = fields.Boolean(
        related="company_id.tbai_enabled", readonly=True)
    tbai_active_date = fields.Date(
        string="TicketBAI active date",
        help="Start date for sending invoices to the tax authorities",
        default=fields.Date.from_string("2022-01-01"))

    @api.onchange("tbai_active_date")
    def onchange_tbai_active_date(self):
        tbai_invoices = self.env["account.invoice"].search(
            [("journal_id", "=", self._origin.id),
                ("tbai_invoice_id", "!=", False)]
        )
        if len(tbai_invoices) > 0:
            raise UserError(_("You cannot change the active date from this journal,"
                              " because at least one invoice has already been sent."))
