# Copyright 2020 Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    @api.multi
    def post_inventory(self):
        if self.company_id.silicie_inventory_disabled:
            for line in self.line_ids:
                if line.product_id.silicie_product_type:
                    raise ValidationError(
                        _('Inventory SILICIE Product is not allowed.'))
        res = super().post_inventory()
        return res
