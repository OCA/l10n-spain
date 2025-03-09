# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# Copyright 2023 Javier Colmenero - (https://javier@comunitea.com)
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

from .misc import FISCAL_ACQUIRERS, FISCAL_MANUFACTURERS, PRODUCT_KEYS


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_plastic_tax = fields.Boolean(
        string="Is plastic tax?",
        tracking=True,
        compute="_compute_plastic_info",
        inverse="_inverse_plastic_info",
        search="_search_is_plastic_tax",
    )
    tax_plastic_type = fields.Selection(
        selection=[
            ("manufacturer", _("Manufacturer")),
            ("acquirer", _("Acquirer")),
            ("both", _("Both")),
        ],
        default="both",
        compute="_compute_plastic_info",
        inverse="_inverse_plastic_info",
        search="_search_tax_plastic_type",
    )
    plastic_type_key = fields.Selection(
        selection=PRODUCT_KEYS,
        string="Plastic type key",
        compute="_compute_plastic_info",
        inverse="_inverse_plastic_info",
        search="_search_plastic_type_key",
    )
    plastic_tax_weight = fields.Float(
        string="Plastic weight",
        digits="Stock Weight",
        compute="_compute_plastic_info",
        inverse="_inverse_plastic_info",
        search="_search_plastic_tax_weight",
    )
    plastic_weight_non_recyclable = fields.Float(
        string="Plastic weight non recyclable",
        digits="Stock Weight",
        compute="_compute_plastic_info",
        inverse="_inverse_plastic_info",
        search="_search_plastic_weight_non_recyclable",
    )
    plastic_tax_regime_manufacturer = fields.Selection(
        selection=FISCAL_MANUFACTURERS,
        string="Plastic tax regime manufaturer",
        compute="_compute_plastic_info",
        inverse="_inverse_plastic_info",
        search="_search_plastic_tax_regime_manufacturer",
    )
    plastic_tax_regime_acquirer = fields.Selection(
        selection=FISCAL_ACQUIRERS,
        string="Plastic tax regime acquirer",
        compute="_compute_plastic_info",
        inverse="_inverse_plastic_info",
        search="_search_plastic_tax_regime_acquirer",
    )

    @api.constrains("plastic_weight_non_recyclable", "plastic_tax_weight")
    def check_plastic_tax_weight(self):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for item in self:
            weight1 = item.plastic_weight_non_recyclable
            weight2 = item.plastic_tax_weight
            if (
                not float_is_zero(weight1, precision_digits=precision)
                and not float_is_zero(weight2, precision_digits=precision)
                and weight1 > weight2
            ):
                raise UserError(
                    _("The non-recyclable weight must be equal to or less than")
                )

    def _search_plastic_field(self, field_name, operator, value):
        products = self.env["product.product"].search(
            [(field_name, operator, value)], limit=None
        )
        return [("id", "in", products.mapped("product_tmpl_id").ids)]

    def _search_is_plastic_tax(self, operator, value):
        return self._search_plastic_field("is_plastic_tax", operator, value)

    def _search_tax_plastic_type(self, operator, value):
        return self._search_plastic_field("tax_plastic_type", operator, value)

    def _search_plastic_type_key(self, operator, value):
        return self._search_plastic_field("plastic_type_key", operator, value)

    def _search_plastic_tax_weight(self, operator, value):
        return self._search_plastic_field("plastic_tax_weight", operator, value)

    def _search_plastic_weight_non_recyclable(self, operator, value):
        return self._search_plastic_field(
            "plastic_weight_non_recyclable", operator, value
        )

    def _search_plastic_tax_regime_manufacturer(self, operator, value):
        return self._search_plastic_field(
            "plastic_tax_regime_manufacturer", operator, value
        )

    def _search_plastic_tax_regime_acquirer(self, operator, value):
        return self._search_plastic_field(
            "plastic_tax_regime_acquirer", operator, value
        )

    @api.depends(
        "product_variant_ids",
        "product_variant_ids.is_plastic_tax",
        "product_variant_ids.tax_plastic_type",
        "product_variant_ids.plastic_type_key",
        "product_variant_ids.plastic_tax_weight",
        "product_variant_ids.plastic_weight_non_recyclable",
        "product_variant_ids.plastic_tax_regime_manufacturer",
        "product_variant_ids.plastic_tax_regime_acquirer",
    )
    def _compute_plastic_info(self):
        self.is_plastic_tax = False
        self.tax_plastic_type = False
        self.plastic_type_key = False
        self.plastic_tax_weight = False
        self.plastic_weight_non_recyclable = False
        self.plastic_tax_regime_manufacturer = False
        self.plastic_tax_regime_acquirer = False
        for item in self.filtered(lambda x: len(x.product_variant_ids) == 1):
            variant = item.product_variant_ids
            item.is_plastic_tax = variant.is_plastic_tax
            item.tax_plastic_type = variant.tax_plastic_type
            item.plastic_type_key = variant.plastic_type_key
            item.plastic_tax_weight = variant.plastic_tax_weight
            item.plastic_weight_non_recyclable = variant.plastic_weight_non_recyclable
            item.plastic_tax_regime_manufacturer = (
                variant.plastic_tax_regime_manufacturer
            )
            item.plastic_tax_regime_acquirer = variant.plastic_tax_regime_acquirer

    def _inverse_plastic_info(self):
        for item in self.filtered(lambda x: len(x.product_variant_ids) == 1):
            variant_info = {
                "is_plastic_tax": item.is_plastic_tax,
                "tax_plastic_type": item.tax_plastic_type,
                "plastic_type_key": item.plastic_type_key,
                "plastic_tax_weight": item.plastic_tax_weight,
                "plastic_weight_non_recyclable": item.plastic_weight_non_recyclable,
                "plastic_tax_regime_manufacturer": item.plastic_tax_regime_manufacturer,
                "plastic_tax_regime_acquirer": item.plastic_tax_regime_acquirer,
            }
            item.product_variant_ids.update(variant_info)
