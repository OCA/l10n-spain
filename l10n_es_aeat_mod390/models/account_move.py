# Copyright 2024 ForgeFlow <contact@forgeflow.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_bankrupcy_uncollectible_debt = fields.Boolean(
        string="Bankrupcy/uncollectible debt",
        help="When this is set, the tax base and rate will "
        "be reflected in fields 31 and 32 of the AEAT 390 model",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
