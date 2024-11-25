# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    company_sii_enabled = fields.Boolean(
        related="company_id.sii_enabled", string="Company enable SII"
    )
    sii_enabled = fields.Boolean(string="Enable SII", default=True)
