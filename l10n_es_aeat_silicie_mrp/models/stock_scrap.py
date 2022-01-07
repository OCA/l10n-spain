# Copyright 2020 Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    silicie_loss_id = fields.Many2one(
        string="Loss SILICIE",
        comodel_name="aeat.loss.silicie",
        ondelete="restrict",
    )
    silicie_move_type_id = fields.Many2one(
        string="Move Type SILICIE",
        comodel_name="aeat.move.type.silicie",
        ondelete="restrict",
    )
    silicie_product_type = fields.Selection(
        related="product_id.silicie_product_type",
        readonly=True,
    )
