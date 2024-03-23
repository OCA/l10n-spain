# © 2022 FactorLibre - Hugo Córdoba <hugo.cordoba@factorlibre.com>
# © 2022 FactorLibre - Luis J. Salvatierra <luis.salvatierra@factorlibre.com>
# © 2023 FactorLibre - Aritz Olea <aritz.olea@factorlibre.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.constrains("total_plastic_weight", "non_reusable_plastic_weight")
    def _check_plastic_weight(self):
        for template in self:
            if template.non_reusable_plastic_weight > template.total_plastic_weight:
                raise ValidationError(
                    _("Non reusable plastic weight cannot exceed total plastic weight.")
                )

    plastic_tax_product_code = fields.Selection(
        selection=[
            ("A", "A - Non-reusable containers containing plastic"),
            (
                "B",
                "B - Semi-finished plastic products intended to obtain type A "
                "plastics",
            ),
            (
                "C",
                "C - Products containing plastic intended to allow closure, "
                "marketing or otherwise of non-reusable packaging",
            ),
        ],
        inverse="_inverse_set_plastic_tax_product_code",
    )
    total_plastic_weight = fields.Float(
        string="Plastic Total Weight",
        inverse="_inverse_set_total_plastic_weight",
        digits="Stock Weight",
    )
    non_reusable_plastic_weight = fields.Float(
        inverse="_inverse_set_non_reusable_plastic_weight",
        digits="Stock Weight",
    )

    def _inverse_set_plastic_tax_product_code(self):
        for variant in self:
            if 1 == len(variant.product_tmpl_id.product_variant_ids) or (
                variant.plastic_tax_product_code
                and not variant.product_tmpl_id.plastic_tax_product_code
            ):
                variant.product_tmpl_id.plastic_tax_product_code = (
                    variant.plastic_tax_product_code
                )

    def _inverse_set_total_plastic_weight(self):
        for variant in self:
            if 1 == len(variant.product_tmpl_id.product_variant_ids) or (
                variant.total_plastic_weight
                and not variant.product_tmpl_id.total_plastic_weight
            ):
                variant.product_tmpl_id.total_plastic_weight = (
                    variant.total_plastic_weight
                )

    def _inverse_set_non_reusable_plastic_weight(self):
        for variant in self:
            if 1 == len(variant.product_tmpl_id.product_variant_ids) or (
                variant.non_reusable_plastic_weight
                and not variant.product_tmpl_id.non_reusable_plastic_weight
            ):
                variant.product_tmpl_id.non_reusable_plastic_weight = (
                    variant.non_reusable_plastic_weight
                )

    def set_plastic_tax_from_template(self):
        for variant in self:
            template = variant.product_tmpl_id
            variant.write(
                {
                    "plastic_tax_product_code": template.plastic_tax_product_code,
                    "total_plastic_weight": template.total_plastic_weight,
                    "non_reusable_plastic_weight": template.non_reusable_plastic_weight,
                }
            )
