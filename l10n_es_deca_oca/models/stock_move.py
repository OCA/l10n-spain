# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    deca_weight = fields.Float(
        compute="_compute_deca_weight",
        digits=False,
        min_display_digits="Stock Weight",
        store=True,
        compute_sudo=True,
        help=(
            "Cargo weight: actual quantity when nonzero, otherwise planned "
            "quantity. Mass units convert to kg; other products use their weight "
            "in Odoo's effective weight unit, converted to kg without rounding. "
            "An invalid effective unit sets derived weights to zero and blocks DeCA. "
            "After changing that setting, existing DeCA weights need recomputation."
        ),
    )

    @api.model
    def _get_deca_weight_uom(self, required=False):
        """Resolve the effective native weight unit without breaking stock computes."""
        try:
            unit = (
                self.env["product.template"]
                ._get_weight_uom_id_from_ir_config_parameter()
                .exists()
            )
        except (ValueError, TypeError):
            unit = self.env["uom.uom"]
        kg = self.env.ref("uom.product_uom_kgm")
        if len(unit) == 1 and unit.category_id == kg.category_id:
            return unit
        if required:
            raise UserError(
                self.env._(
                    "The effective product weight unit is invalid. Configure an "
                    "existing weight unit before generating a DeCA."
                )
            )
        _logger.warning(
            "Invalid effective product weight unit: non-mass DeCA weights "
            "set to zero for this compute batch"
        )
        return self.env["uom.uom"]

    @api.depends(
        "product_id.weight",
        "product_id.uom_id",
        "product_id.uom_id.factor",
        "product_id.uom_id.category_id",
        "product_id.uom_id.rounding",
        "product_uom_qty",
        "product_uom.factor",
        "product_uom.rounding",
        "quantity",
    )
    def _compute_deca_weight(self):
        uom_kgm = self.env.ref("uom.product_uom_kgm")
        weight_uom = self._get_deca_weight_uom()
        for move in self:
            product_qty = move.product_qty
            if move.quantity:
                product_qty = move.product_uom._compute_quantity(
                    move.quantity, move.product_id.uom_id, rounding_method="HALF-UP"
                )
            if move.product_id.uom_id.category_id == uom_kgm.category_id:
                weight = move.product_id.uom_id._compute_quantity(
                    product_qty, uom_kgm, round=False
                )
            elif weight_uom:
                weight = weight_uom._compute_quantity(
                    product_qty * move.product_id.weight, uom_kgm, round=False
                )
            else:
                weight = 0.0
            move.deca_weight = weight
