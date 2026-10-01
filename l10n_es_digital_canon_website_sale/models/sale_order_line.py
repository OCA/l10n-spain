# Copyright 2026 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("product_id", "company_id")
    def _compute_tax_id(self):
        res = super()._compute_tax_id()
        for line in self:
            product = line.product_id
            partner = line._get_digital_canon_partner()
            if (
                line.tax_id
                and line.order_id.website_id
                and product.l10n_es_digital_canon
                and not partner.country_id
                and not partner.is_digital_canon_exempt
            ):
                line.tax_id |= line.env.ref(
                    f"account.{line.company_id.id}_tax_template_canon_sale_"
                    f"{product.l10n_es_digital_canon.split('.')[0]}",
                    raise_if_not_found=False,
                )
        return res
