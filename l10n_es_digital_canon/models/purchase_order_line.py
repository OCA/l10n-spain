# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _compute_tax_id(self):
        res = super()._compute_tax_id()
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
        return res
