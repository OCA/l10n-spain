# Copyright 2026 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, exceptions, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def contrast_aeat(self):
        invalid_invoices = self.filtered(
            lambda invoice: not invoice.sii_csv
            or not invoice.sii_enabled
            or invoice.aeat_state != "sent"
            or invoice.state != "posted"
        )
        if invalid_invoices:
            raise exceptions.UserError(
                _(
                    "The invoices must be posted and have a CSV in order to be matched."
                    "\nNon-matchable invoices: %(invoice_names)s",
                    invoice_names=", ".join(i.name for i in invalid_invoices),
                )
            )
        return super().contrast_aeat()
