# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_caser_insurance = fields.Boolean(copy=False)
    caser_insure_quantity = fields.Integer(string="Quantity to Insure", copy=False)
    caser_insured_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Insured Product Line",
        copy=False,
        ondelete="set null",
    )
    caser_lot_id = fields.Many2one(
        "stock.lot", string="Insured Lot", readonly=True, copy=False
    )
    caser_request_xml = fields.Text(readonly=True, copy=False)
    caser_response_xml = fields.Text(readonly=True, copy=False)
    caser_policy_number = fields.Char(readonly=True, copy=False)
    caser_insurance_price = fields.Float(
        string="Insurance Price", readonly=True, copy=False, digits=(16, 2)
    )
    caser_error_message = fields.Text(readonly=True, copy=False)

    @api.onchange("caser_insure_quantity")
    def _onchange_caser_insure_quantity(self):
        if self.caser_insure_quantity > self.product_uom_qty:
            raise ValidationError(
                self.env._(
                    "Insured qty (%(insured)s) cannot exceed product qty "
                    "(%(product)s)"
                )
                % {
                    "insured": self.caser_insure_quantity,
                    "product": self.product_uom_qty,
                }
            )

    def unlink(self):
        orders = self.filtered(lambda line: not line.is_caser_insurance).mapped(
            "order_id"
        )
        res = super().unlink()
        for order in orders:
            order.order_line._sync_caser_insurance_lines()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._sync_caser_insurance_lines()
        return lines

    def write(self, vals):
        # Prevent manual quantity changes on insurance lines; their qty is
        # always 1 and managed entirely by _sync_caser_insurance_lines.
        if "product_uom_qty" in vals and self.filtered("is_caser_insurance"):
            raise ValidationError(
                self.env._(
                    "The quantity of a Caser insurance line"
                    " cannot be modified manually."
                )
            )
        if "product_uom_qty" in vals:
            # Cap caser_insure_quantity to the new product qty so we never
            # insure more units than are actually in the order.
            new_qty = int(vals["product_uom_qty"])
            to_cap = self.filtered(lambda line: line.caser_insure_quantity > new_qty)
            if to_cap:
                super(SaleOrderLine, to_cap).write(
                    dict(vals, caser_insure_quantity=new_qty)
                )
                remaining = self - to_cap
                if remaining:
                    super(SaleOrderLine, remaining).write(vals)
                self._sync_caser_insurance_lines()
                return True
        res = super().write(vals)
        self._sync_caser_insurance_lines()
        return res

    def _sync_caser_insurance_lines(self):
        # Ensure each product line that requests insurance has exactly
        # caser_insure_quantity insurance lines linked to it, one per unit.
        for order in self.mapped("order_id"):
            product_lines = order.order_line.filtered(
                lambda line: not line.is_caser_insurance
                and line.product_id
                and line.caser_insure_quantity > 0
            )
            for sale_line in product_lines:
                insurance_product = self._get_insurance_product_for_price(
                    sale_line.price_reduce_taxinc,
                    sale_line.product_id.categ_id.caser_asset_type,
                )
                if not insurance_product:
                    continue
                existing = order.order_line.filtered(
                    lambda line, sl=sale_line: line.is_caser_insurance
                    and line.caser_insured_line_id == sl
                )
                self._adjust_insurance_lines(
                    order,
                    insurance_product,
                    sale_line.caser_insure_quantity,
                    existing,
                    insured_line=sale_line,
                )
            # Remove orphaned insurance lines (their product line was removed
            # or no longer needs insurance).
            for ins_line in order.order_line.filtered(
                lambda line: line.is_caser_insurance
            ):
                if ins_line.caser_insured_line_id not in product_lines:
                    ins_line.unlink()

    def action_retry_caser_insurance(self):
        self.ensure_one()
        if self.caser_policy_number:
            raise ValidationError(
                self.env._("Caser policy already registered: %s")
                % self.caser_policy_number
            )
        picking = self.order_id.picking_ids.filtered(lambda p: p.state == "done")
        picking[0]._send_caser_insurance_request(self)

    def _get_insurance_product_for_price(self, price, asset_type=None):
        return self.env["caser.price.range"].get_insurance_product_for_price(
            price, asset_type
        )

    def _adjust_insurance_lines(
        self, order, insurance_product, quantity, existing, insured_line=None
    ):
        # Bring the number of insurance lines for a given product line in line
        # with the requested quantity: remove excess or create missing ones.
        if quantity == 0:
            existing.unlink()
            return
        current = len(existing)
        if current > quantity:
            self._remove_excess_lines(existing, current - quantity)
        elif current < quantity:
            self._create_missing_lines(
                order,
                insurance_product,
                quantity - current,
                insured_line=insured_line,
            )

    def _remove_excess_lines(self, lines, count):
        without_lots = lines.filtered(lambda line: not line.caser_lot_id)[:count]
        if len(without_lots) < count:
            with_lots = lines[: count - len(without_lots)]
            without_lots |= with_lots
        without_lots.unlink()

    def _create_missing_lines(self, order, insurance_product, count, insured_line=None):
        for _ in range(count):
            self.create(
                {
                    "order_id": order.id,
                    "product_id": insurance_product.id,
                    "product_uom_qty": 1,
                    "price_unit": insurance_product.list_price,
                    "is_caser_insurance": True,
                    "caser_insured_line_id": insured_line.id if insured_line else False,
                }
            )
