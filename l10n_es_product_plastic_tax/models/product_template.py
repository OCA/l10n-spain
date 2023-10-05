# © 2022 FactorLibre - Hugo Córdoba <hugo.cordoba@factorlibre.com>
# © 2023 FactorLibre - Luis J. Salvatierra <luis.salvatierra@factorlibre.com>
# © 2023 FactorLibre - Aritz Olea <aritz.olea@factorlibre.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

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

    def _create_variant_ids(self):
        template_variants = {}
        for template in self.with_context(active_test=False):
            template_variants[template] = template.product_variant_ids
        res = super()._create_variant_ids()
        for template, existing_variants in template_variants.items():
            to_update_variants = template.product_variant_ids - existing_variants
            if 0 < len(to_update_variants):
                to_update_variants.set_plastic_tax_from_template()
        return res

    def _inverse_set_plastic_tax_product_code(self):
        for template in self:
            template.product_variant_ids.filtered(
                lambda x, t=template: x.plastic_tax_product_code
                != t.plastic_tax_product_code
            ).write({"plastic_tax_product_code": template.plastic_tax_product_code})

    def _inverse_set_total_plastic_weight(self):
        for template in self:
            template.product_variant_ids.filtered(
                lambda x, t=template: x.total_plastic_weight != t.total_plastic_weight
            ).write({"total_plastic_weight": template.total_plastic_weight})

    def _inverse_set_non_reusable_plastic_weight(self):
        for template in self:
            template.product_variant_ids.filtered(
                lambda x, t=template: x.non_reusable_plastic_weight
                != t.non_reusable_plastic_weight
            ).write(
                {"non_reusable_plastic_weight": template.non_reusable_plastic_weight}
            )
