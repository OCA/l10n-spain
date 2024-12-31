# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sigaus_amount_subtotal = fields.Monetary(
        compute="_compute_sigaus_amount", compute_sudo=True
    )
    sigaus_amount_tax = fields.Monetary(
        compute="_compute_sigaus_amount", compute_sudo=True
    )
    sigaus_amount_total = fields.Monetary(
        compute="_compute_sigaus_amount", compute_sudo=True
    )
    picking_total_with_sigaus = fields.Monetary(
        compute="_compute_sigaus_amount", compute_sudo=True
    )

    @api.depends(
        "amount_total",
        "move_line_ids.sigaus_amount_subtotal",
        "move_line_ids.sigaus_amount_tax",
        "move_line_ids.sigaus_amount_total",
    )
    def _compute_sigaus_amount(self):
        for pick in self:
            sigaus_amount_subtotal = sigaus_amount_tax = sigaus_amount_total = 0.0
            for line in pick.move_line_ids:
                sigaus_amount_subtotal += line.sigaus_amount_subtotal
                sigaus_amount_tax += line.sigaus_amount_tax
                sigaus_amount_total += line.sigaus_amount_total
            pick.sigaus_amount_subtotal = sigaus_amount_subtotal
            pick.sigaus_amount_tax = sigaus_amount_tax
            pick.sigaus_amount_total = sigaus_amount_total
            pick.picking_total_with_sigaus = (
                pick.sigaus_amount_total + pick.amount_total
            )
