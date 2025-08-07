# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    def map_tax(self, taxes, product=None, partner=None):
        taxes = super().map_tax(taxes, product=product, partner=partner)
        if product:
            if (
                product.l10n_es_digital_canon
                and partner.country_id == self.env.ref("base.es")
                and not partner.is_digital_canon_exempt
            ):
                ttype = (
                    "sale" if taxes and taxes[0].type_tax_use == "sale" else "purchase"
                )
                tax = self.env.ref(
                    f"l10n_es_digital_canon.{self.company_id.id}_tax_template_canon_{ttype}_"
                    f"{product.l10n_es_digital_canon.split('.')[0]}",
                    raise_if_not_found=False,
                )
                if tax:
                    taxes |= tax
        return taxes
