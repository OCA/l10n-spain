# Copyright 2020 Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    scrap_type = fields.Selection(
        selection=[
            ('processing', 'Processing'),
            ('bottling', 'Bottling'),
            ('reception', 'Reception'),
        ],
    )
