# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    deca_weight = fields.Float(
        compute="_compute_deca_weight",
        digits="Stock Weight",
        store=True,
        compute_sudo=True,
    )

    @api.depends("product_id", "product_uom_qty", "product_uom", "quantity", "state")
    def _compute_deca_weight(self):
        uom_kgm = self.env.ref("uom.product_uom_kgm")
        for move in self:
            product_qty = move.product_qty
            if move.quantity:
                product_qty = move.product_uom._compute_quantity(
                    move.quantity, move.product_id.uom_id, rounding_method="HALF-UP"
                )
            if move.product_uom._has_common_reference(uom_kgm):
                weight = move.product_uom._compute_quantity(product_qty, uom_kgm)
            else:
                weight = product_qty * move.product_id.weight
            move.deca_weight = weight
