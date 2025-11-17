# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # pylint:disable=missing-return
    @api.depends("product_id", "company_id")
    def _compute_tax_id(self):
        super()._compute_tax_id()
        for line in self:
            taxes = line.tax_id
            product = line.product_id
            partner = line.order_id.partner_shipping_id
            company = line.company_id
            if not taxes or not product or not partner:
                continue
            if (
                product.l10n_es_digital_canon
                and partner.country_id == line.env.ref("base.es")
                and not partner.is_digital_canon_exempt
            ):
                ttype = "sale" if taxes[0].type_tax_use == "sale" else "purchase"
                tax = line.env.ref(
                    f"account.{company.id}_tax_template_canon_{ttype}_"
                    f"{product.l10n_es_digital_canon.split('.')[0]}",
                    raise_if_not_found=False,
                )
                if tax:
                    line.tax_id |= tax
