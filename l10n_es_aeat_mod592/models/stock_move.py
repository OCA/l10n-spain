# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = "stock.move"

    product_plastic_tax_weight = fields.Float(
        related="product_id.product_plastic_tax_weight", store=True
    )
    product_plastic_weight_non_recyclable = fields.Float(
        related="product_id.product_plastic_weight_non_recyclable", store=True
    )
    product_plastic_type_key = fields.Selection(
        related="product_id.product_plastic_type_key", store=True
    )
    product_plastic_concept_manufacturer = fields.Selection(
        [
            ("1", _("(1) Initial existence")),
            ("2", _("(2) Manufacturing")),
            (
                "3",
                _(
                    "(3) Return of products for destruction or reincorporation into the manufacturing process"
                ),
            ),
            ("4", _("(4) Delivery or making available of the products accounted for")),
            (
                "5",
                _(
                    "(5) Other cancellations of the products accounted for other than their delivery or availability"
                ),
            ),
        ],
        string=_("Product Concept Manufacturer"),
        default="1",
    )
    product_plastic_concept_acquirer = fields.Selection(
        [
            ("1", _("(1) Intra-community acquisition")),
            ("2", _("(2) Shipping outside Spanish territory")),
            ("3", _("(3) Inadequacy or destruction")),
            (
                "4",
                _(
                    "(4) Return for destruction or reincorporation into the manufacturing process"
                ),
            ),
        ],
        string=_("Product Concept Acquirer"),
        default="2",
    )
    product_plastic_tax_regime_manufacturer = fields.Selection(
        related="product_id.product_plastic_tax_regime_manufacturer", store=True
    )
    product_plastic_tax_regime_acquirer = fields.Selection(
        related="product_id.product_plastic_tax_regime_manufacturer", store=True
    )
    product_plastic_tax_description = fields.Char(_("Supporting document"), store=True)

    is_plastic_tax = fields.Boolean(
        related="product_id.is_plastic_tax", tracking=True, store=True
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            if line.is_plastic_tax:
                # LINEAS FABRICANTES SIN STOCK ACTUAL
                line.update({"product_plastic_tax_description": line.picking_id.name})
                if self.picking_id.company_plastic_type == "manufacturer":
                    if self.picking_id.picking_type_code == "out_invoice":
                        line.update({"product_plastic_concept_manufacturer": "4"})
                    if self.picking_id.picking_type_code == "out_refund":
                        line.update({"product_plastic_concept_manufacturer": "3"})
                    if self.picking_id.picking_type_code == "incoming":
                        line.update({"product_plastic_concept_manufacturer": "1"})
                    if self.picking_id.picking_type_code == "in_refund":
                        line.update({"product_plastic_concept_manufacturer": "4"})
                if self.picking_id.company_plastic_type == "acquirer":
                    if (
                        self.picking_id.picking_type_code == "out_invoice"
                        and self.partner_id.product_plastic_document_type == "2"
                        and self.partner_id.product_plastic_document_type == "3"
                    ):
                        line.update({"product_plastic_concept_acquirer": "2"})
                    if self.picking_id.picking_type_code == "out_refund":
                        line.update({"product_plastic_concept_acquirer": "4"})
                    if self.picking_id.picking_type_code == "in_invoice":
                        line.update({"product_plastic_concept_acquirer": "1"})
                    if self.picking_id.picking_type_code == "in_refund":
                        line.update({"product_plastic_concept_acquirer": "4"})
        # return res
