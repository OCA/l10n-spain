# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    l10n_es_digital_canon = fields.Selection(
        selection=lambda self: self.env["product.product"]
        ._fields["l10n_es_digital_canon"]
        .selection,
        string="Digital Canon Category",
        compute="_compute_l10n_es_digital_canon",
        inverse="_inverse_l10n_es_digital_canon",
        search="_search_l10n_es_digital_canon",
    )

    @api.depends("product_variant_ids", "product_variant_ids.l10n_es_digital_canon")
    def _compute_l10n_es_digital_canon(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.l10n_es_digital_canon = (
                    template.product_variant_ids.l10n_es_digital_canon
                )
            else:
                template.l10n_es_digital_canon = False

    def _inverse_l10n_es_digital_canon(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.l10n_es_digital_canon = (
                    template.l10n_es_digital_canon
                )

    def _search_l10n_es_digital_canon(self, operator, value):
        products = self.env["product.product"].search(
            [("l10n_es_digital_canon", operator, value)]
        )
        return [("id", "in", products.mapped("product_tmpl_id").ids)]
