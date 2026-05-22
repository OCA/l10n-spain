# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    # pylint:disable=missing-return
    def _compute_tax_id(self):
        super()._compute_tax_id()
        for line in self:
            taxes = line.taxes_id
            product = line.product_id
            partner = line.order_id.partner_id
            company = line.company_id
            if not taxes or not product or not partner:
                continue
            if (
                product.l10n_es_digital_canon
                and partner.country_id == line.env.ref("base.es")
                and not partner.is_digital_canon_exempt
            ):
                tax = line.env.ref(
                    f"account.{company.id}_tax_template_canon_purchase_"
                    f"{product.l10n_es_digital_canon.split('.')[0]}",
                    raise_if_not_found=False,
                )
                if tax:
                    line.taxes_id |= tax

    @api.model
    def _prepare_purchase_order_line(
        self, product_id, product_qty, product_uom, company_id, supplier, po
    ):
        vals = super()._prepare_purchase_order_line(
            product_id, product_qty, product_uom, company_id, supplier, po
        )
        if product_id.l10n_es_digital_canon:
            virtual_line = self.new(vals)
            virtual_line._compute_tax_id()
            vals["taxes_id"] = [(6, 0, virtual_line.taxes_id.ids)]
        return vals
