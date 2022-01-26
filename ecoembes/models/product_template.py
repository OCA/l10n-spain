# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ecoembes_product_master = fields.Char(
        string="Product master",
        compute="_compute_ecoembes_info",
        inverse="_inverse_ecoembes_info",
    )
    ecoembes_date_expiry = fields.Date(
        string="Date expiry",
        compute="_compute_ecoembes_info",
        inverse="_inverse_ecoembes_info",
    )
    ecoembes_sig = fields.Boolean(
        string="SIG/NOSIG option",
        compute="_compute_ecoembes_info",
        inverse="_inverse_ecoembes_info",
    )
    ecoembes_comment = fields.Text(
        string="Comments",
        compute="_compute_ecoembes_info",
        inverse="_inverse_ecoembes_info",
    )
    weight_net_gram_round = fields.Integer(
        string="Weight (g)",
        compute="_compute_ecoembes_info",
        inverse="_inverse_ecoembes_info",
    )
    composition_ids = fields.One2many(
        comodel_name="product.composition",
        inverse_name="product_tmpl_id",
        string="Compositions",
    )

    @api.depends(
        "product_variant_ids",
        "product_variant_ids.ecoembes_product_master",
        "product_variant_ids.ecoembes_date_expiry",
        "product_variant_ids.ecoembes_sig",
        "product_variant_ids.ecoembes_comment",
        "product_variant_ids.weight_net_gram_round",
    )
    def _compute_ecoembes_info(self):
        self.ecoembes_product_master = False
        self.ecoembes_date_expiry = False
        self.ecoembes_sig = False
        self.ecoembes_comment = False
        self.weight_net_gram_round = False
        for item in self.filtered(lambda x: len(x.product_variant_ids) == 1):
            variant = item.product_variant_ids
            item.ecoembes_product_master = variant.ecoembes_product_master
            item.ecoembes_date_expiry = variant.ecoembes_date_expiry
            item.ecoembes_sig = variant.ecoembes_sig
            item.ecoembes_comment = variant.ecoembes_comment
            item.weight_net_gram_round = variant.weight_net_gram_round

    def _inverse_ecoembes_info(self):
        for item in self.filtered(lambda x: len(x.product_variant_ids) == 1):
            variant = {}
            variant.update(
                {
                    "ecoembes_product_master": item.ecoembes_product_master,
                    "ecoembes_date_expiry": item.ecoembes_date_expiry,
                    "ecoembes_sig": item.ecoembes_sig,
                    "ecoembes_comment": item.ecoembes_comment,
                    "weight_net_gram_round": item.weight_net_gram_round,
                }
            )
            item.product_variant_ids.update(variant)
