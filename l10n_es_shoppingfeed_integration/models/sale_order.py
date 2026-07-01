# Copyright 2026 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _shoppingfeed_find_existing_partner(self, vals, store):
        existing = super()._shoppingfeed_find_existing_partner(vals, store)
        if existing or not vals.get("aeat_identification"):
            return existing
        return self.env["res.partner"].search(
            [
                ("aeat_identification", "=", vals["aeat_identification"]),
                ("aeat_identification_type", "=", vals["aeat_identification_type"]),
                ("parent_id", "=", False),
                ("company_id", "in", [store.company_id.id, False]),
            ],
            limit=1,
        )

    @api.model
    def _shoppingfeed_prepare_invalid_vat_vals(self, vals, vat):
        res = super()._shoppingfeed_prepare_invalid_vat_vals(vals, vat)
        vals.update(
            {
                "aeat_identification": vat,
                "aeat_identification_type": "06",
            }
        )
        return res
