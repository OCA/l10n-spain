#  Copyright 2021 Landoo Sistemas de Informacion SL
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    tbai_enabled = fields.Boolean(related="company_id.tbai_enabled", readonly=True)

    @api.onchange("refund_sequence")
    def onchange_refund_sequence(self):
        if not self.refund_sequence and self.type == "sale":
            self.refund_sequence = True

    @api.onchange("type")
    def onchange_type(self):
        if self.type == "sale":
            self.refund_sequence = True
