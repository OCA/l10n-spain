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
        journals = self.filtered(lambda journal: journal.type in ("sale", "purchase"))
        if not journals:
            return res
        AccountMove = self.env["account.move"]
        domain_base = [
            ("journal_id", "in", journals.ids),
            ("sii_enabled", "=", True),
            "|",
            "&",
            ("aeat_state", "=", "not_sent"),
            ("state", "=", "posted"),
            ("aeat_send_failed", "=", True),
        ]
        all_data = AccountMove._read_group(
            domain_base, ["journal_id", "aeat_state", "aeat_send_failed"], ["__count"]
        )
        for journal_id, aeat_state, aeat_send_failed, count in all_data:
            journal_dict = dashboard_data[journal_id.id]
            if not journal_dict.get("number_not_sent"):
                journal_dict["number_not_sent"] = 0
            if not journal_dict.get("number_aeat_failed"):
                journal_dict["number_aeat_failed"] = 0
            if aeat_state == "not_sent":
                journal_dict["number_not_sent"] += count
            if aeat_send_failed:
                journal_dict["number_aeat_failed"] += count
        return res
