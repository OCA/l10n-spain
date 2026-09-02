# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProductBrand(models.Model):
    _inherit = "product.brand"

    caser_mobile_code = fields.Char(
        string="Caser Code (Mobile)",
        help="Brand code sent to Caser API for mobile phone policies "
        "(asset type 200021)",
    )
    caser_tablet_code = fields.Char(
        string="Caser Code (Tablet)",
        help="Brand code sent to Caser API for tablet policies (asset type 262)",
    )

    _CASER_ASSET_TYPE_CODE_FIELD = {
        "200021": "caser_mobile_code",
        "262": "caser_tablet_code",
    }

    def _get_caser_code(self, asset_type):
        """Caser brand code for the given asset type, or False if unset/no brand."""
        if not self:
            return False
        self.ensure_one()
        field_name = self._CASER_ASSET_TYPE_CODE_FIELD.get(asset_type)
        return self[field_name] if field_name else False
