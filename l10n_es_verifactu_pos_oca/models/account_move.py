# Copyright 2026 MDSX - Manuel Diez Silva
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_verifactu_substituted_documents(self):
        """A ticket invoiced afterwards is substituted, not invoiced again.

        Pressing "Invoice" on a POS order that was already registered as a
        simplified invoice (F2) issues an ordinary invoice in substitution of
        it, so it must be registered as F3 quoting the ticket. Sending it as a
        regular F1 would declare the very same operation twice.

        Orders invoiced from the start never got a simplified invoice number
        and so have no VERI*FACTU entry: they are not substituting anything and
        keep producing a regular F1.
        """
        documents = super()._get_verifactu_substituted_documents()
        return documents + list(
            self.sudo().pos_order_ids.filtered("last_verifactu_invoice_entry_id")
        )
