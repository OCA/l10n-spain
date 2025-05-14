# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    invoice_summary_id = fields.Many2one(
        "account.move",
    )
