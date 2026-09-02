# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

from .caser_asset_types import CASER_ASSET_TYPES, CASER_PROTOCOL_BY_ASSET_TYPE


class ProductCategory(models.Model):
    _inherit = "product.category"

    caser_asset_type = fields.Selection(
        selection=CASER_ASSET_TYPES,
        help="Asset type code for Caser insurance (200021=Phone, 262=Tablet)",
    )
    caser_protocol = fields.Char(
        compute="_compute_caser_protocol",
        store=True,
        help="Protocol code determined by asset type (61680=Phone, 61681=Tablet)",
    )

    @api.depends("caser_asset_type")
    def _compute_caser_protocol(self):
        for record in self:
            record.caser_protocol = CASER_PROTOCOL_BY_ASSET_TYPE.get(
                record.caser_asset_type, False
            )
