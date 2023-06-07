# Copyright 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_subtotal_without_discount(self):
        self.ensure_one()
        if self.display_type != "product":
            return 0
        subtotal = self.quantity * self.price_unit
        if self.tax_ids:
            taxes_res = self.tax_ids.compute_all(
                self.price_unit,
                quantity=self.quantity,
                currency=self.currency_id,
                product=self.product_id,
                partner=self.partner_id,
                is_refund=self.is_refund,
            )
            return taxes_res["total_excluded"]
        else:
            return subtotal
