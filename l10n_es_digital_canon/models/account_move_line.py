# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_computed_taxes(self):
        self.ensure_one()
        taxes = super()._get_computed_taxes()
        if (
            self.move_id.partner_id.country_id == self.env.ref("base.es")
            and not self.move_id.partner_id.is_digital_canon_exempt
        ):
            ttype = "sale" if taxes.type_tax_use == "sale" else "purchase"
            if self.product_id.l10n_es_digital_canon:
                tax = self.env.ref(
                    f"l10n_es_digital_canon.{self.company_id.id}_tax_template_canon_{ttype}_"
                    f"{self.product_id.l10n_es_digital_canon.split('.')[0]}",
                    raise_if_not_found=False,
                )
                if tax:
                    taxes |= tax
        return taxes
