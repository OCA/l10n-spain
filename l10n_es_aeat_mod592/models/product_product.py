# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# Copyright 2023 Javier Colmenero - (https://javier@comunitea.com)
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

from .misc import FISCAL_ACQUIRERS, FISCAL_MANUFACTURERS, PRODUCT_KEYS


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_plastic_tax = fields.Boolean(string="Is plastic tax?", tracking=True)
    tax_plastic_type = fields.Selection(
        selection=[
            ("manufacturer", _("Manufacturer")),
            ("acquirer", _("Acquirer")),
            ("both", _("Both")),
        ],
        default="both",
    )
    plastic_type_key = fields.Selection(
        selection=PRODUCT_KEYS, string="Plastic type key"
    )
    plastic_tax_weight = fields.Float(
        string="Plastic weight",
        digits="Stock Weight",
    )
    plastic_weight_non_recyclable = fields.Float(
        string="Plastic weight non recyclable",
        digits="Stock Weight",
    )
    plastic_tax_regime_manufacturer = fields.Selection(
        selection=FISCAL_MANUFACTURERS,
        string="Plastic tax regime manufaturer",
    )
    plastic_tax_regime_acquirer = fields.Selection(
        selection=FISCAL_ACQUIRERS,
        string="Plastic tax regime acquirer",
    )

    @api.constrains("plastic_weight_non_recyclable", "plastic_tax_weight")
    def check_plastic_weight_non_recyclable(self):
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
