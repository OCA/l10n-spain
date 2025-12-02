# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    caser_asset_type = fields.Selection(
        selection=[
            ("200021", "Teléfono Móvil"),
            ("262", "Tablet"),
        ],
        help="Asset type code for Caser insurance (200021=Phone, 262=Tablet)",
    )
    caser_protocol = fields.Char(
        compute="_compute_caser_protocol",
        store=True,
        help="Protocol code determined by asset type (61680=Phone, 61681=Tablet)",
    )

    @api.depends("caser_asset_type")
    def _compute_caser_protocol(self):
        protocol_mapping = {
            "200021": "61680",  # Teléfono Móvil → Daños y Robo Telefonia-Tablets
            "262": "61681",  # Tablet → Daños y Robo Tablets
        }
        for record in self:
            record.caser_protocol = protocol_mapping.get(record.caser_asset_type, False)
