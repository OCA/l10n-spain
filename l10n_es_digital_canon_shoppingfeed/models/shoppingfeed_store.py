# Copyright 2026 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ShoppingfeedStore(models.Model):
    _inherit = "shoppingfeed.store"

    include_l10n_es_canon_taxes_in_price = fields.Boolean(
        string="Include Digital Canon Taxes in Price",
        default=False,
        tracking=True,
        help="If enabled, the exported price will include digital canon taxes.",
    )
