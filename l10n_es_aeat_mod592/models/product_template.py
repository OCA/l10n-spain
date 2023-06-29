# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Copyright 2023 Javier Colmenero - (https://javier@comunitea.com)

from odoo import api, fields, models, exceptions, _


class ProductTemplate(models.Model):

    _description = "Product Template"
    _inherit = "product.template"

    is_plastic_tax = fields.Boolean("Is plastic tax?",  tracking=True)
    product_plastic_tax_weight = fields.Float("Product plastic weight")
    product_plastic_weight_non_recyclable = fields.Float(
        "Product plastic weight non recyclable"
    )
    product_plastic_type_key = fields.Selection(
        [
            ("A", _("(A) Non-reusable")),
            ("B", _("(B) Semi-finished")),
            ("C", _("(C) Plastic product intended to allow the closure")),
        ],
        string="Product plastic type key")

    product_plastic_tax_regime_manufacturer = fields.Selection(
        [
            ("A", _("(A) Subjection and non-exemption ")),
            ("B", _("(B) Not subject to article 73 a) Law 7/2022, of April 8")),
            ("C", _("(C) Not subject to article 73 b) Law 7/2022, of April 8")),
            ("D", _("(D) Non-subjection article 73 c) Law 7/2022, of April 8")),
            ("E", _("(E) Not subject to article 73 d) Law 7/2022, of April 8")),
            ("F", _("(F) Exemption article 75 a) 1º Law 7/2022, of April 8")),
            ("G", _("(G) Exemption article 75 a) 2º Law 7/2022, of April 8")),
            ("H", _("(H) Exemption article 75 a) 3º Law 7/2022, of April 8")),
            ("I", _("(I) Exemption article 75 c) Law 7/2022, of April 8")),
            ("J", _("(J) Exemption article 75 g) 1º Law 7/2022, of April 8")),
            ("K", _("(K) Exemption article 75 g) 2º Law 7/2022, of April 8")),
        ],
        string="Product tax regime manufaturer",
    )

    product_plastic_tax_regime_acquirer = fields.Selection(
        [
            ("A", _("(A) Subjection and non-exemption Law 7/2022, of April 8")),
            ("B", _("(B) Non-subjection article 73 c) Law 7/2022, of April 8")),
            ("C", _("(C) Not subject to article 73 d) Law 7/2022, of April 8")),
            ("D", _("(D) Exemption article 75 a) 1º Law 7/2022, of April 8")),
            ("E", _("(E) Exemption article 75 a) 2º Law 7/2022, of April 8")),
            ("F", _("(F) Exemption article 75 a) 3º Law 7/2022, of April 8")),
            ("G", _("(G) Exemption article 75 b) Law 7/2022, of April 8")),
            ("H", _("(H) Exemption article 75 c) Law 7/2022, of April 8")),
            ("I", _("(I) Exemption article 75 d) Law 7/2022, of April 8")),
            ("J", _("(J) Exemption article 75 e) Law 7/2022, of April 8")),
            ("K", _("(K) Exemption article 75 f) Law 7/2022, of April 8")),
            ("L", _("(L) Exemption article 75 g) 1º Law 7/2022, of April 8")),
            ("M", _("(M) Exemption article 75 g) 2º Law 7/2022, of April 8")),
        ],
        string="Product tax regime acquirer",
    )

    tax_plastic_type = fields.Selection([
        ('manufacturer', _('Manufacturer')),
        ('acquirer', _('Acquirer')),
        ('both', _('Both')),
    ],
        string='Tax Plastic Type',
        default='both'
    )

    @api.onchange('product_plastic_weight_non_recyclable')
    def _onchange_product_plastic_weight_non_recyclable(self):
        if self.product_plastic_weight_non_recyclable > self.product_plastic_tax_weight:
            raise exceptions.UserError(
                _(
                    "The non-recyclable weight must be equal to or less than"
                )
            )
