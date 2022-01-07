# Copyright 2020 Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    density = fields.Float(
        string="Densidad SILICIE (Kg / m3)",
        digits=(3, 3),
    )
    extract = fields.Float(
        string="Extracto SILICIE",
    )
    silicie_product_type = fields.Selection(
        related="product_id.silicie_product_type",
        readonly=True,
        store=True,
    )
