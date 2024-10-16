# Copyright 2017 FactorLibre - Janire Olagibel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    ecoembes_product_master = fields.Char(string="Product master")
    ecoembes_date_expiry = fields.Date(string="Date expiry")
    ecoembes_sig = fields.Boolean(string="SIG/NOSIG option")
    ecoembes_comment = fields.Text(string="Comments")
    weight_net_gram_round = fields.Integer(
        string="Weight (g)", compute="_compute_weight_net_gram_round", store=True
    )
    composition_ids = fields.One2many(
        comodel_name="product.composition",
        inverse_name="product_id",
        string="Compositions",
    )

    @api.depends("weight")
    def _compute_weight_net_gram_round(self):
        for item in self:
            item.weight_net_gram_round = round(item.weight * 1000)
