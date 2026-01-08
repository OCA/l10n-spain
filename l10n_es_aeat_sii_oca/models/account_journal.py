# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    company_sii_enabled = fields.Boolean(
        related="company_id.sii_enabled", string="Company enable SII"
    )
    sii_enabled = fields.Boolean(string="Enable SII", default=True)

    def _fill_sale_purchase_dashboard_data(self, dashboard_data):
        res = super()._fill_sale_purchase_dashboard_data(dashboard_data)
        for journal in self.filtered(
            lambda journal: journal.type in ("sale", "purchase")
        ):
            domain_not_send = [
                ("journal_id", "=", journal.id),
                ("aeat_state", "=", "not_sent"),
                ("sii_enabled", "=", True),
            ]
            domain_fail = [
                ("journal_id", "=", journal.id),
                ("aeat_send_failed", "=", True),
                ("sii_enabled", "=", True),
            ]
            journal_dict = dashboard_data[journal.id]
            AccountMove = self.env["account.move"]
            journal_dict["number_not_sent"] = AccountMove.search_count(domain_not_send)
            journal_dict["number_aeat_failed"] = AccountMove.search_count(domain_fail)
        return res
