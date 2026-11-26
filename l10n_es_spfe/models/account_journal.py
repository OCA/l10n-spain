# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    spfe_enabled = fields.Boolean(
        string="SPFE Enabled",
        default=True,
        help="Include invoices posted in this journal in AEAT SPFE.",
    )
