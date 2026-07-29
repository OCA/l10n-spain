# Copyright 2026 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _get_website_digital_canon_tax(self, product_or_template, website=None):
        """Return the digital canon sale tax to include in website prices, if any."""
        website = website or self.env["website"].get_current_website()
        if website.show_line_subtotals_tax_selection != "tax_included":
            return self.env["account.tax"]
        canon = product_or_template.sudo().l10n_es_digital_canon
        if not canon:
            return self.env["account.tax"]
        partner = self.env.user.partner_id
        if partner.is_digital_canon_exempt or (
            partner.country_id and partner.country_id != self.env.ref("base.es")
        ):
            return self.env["account.tax"]
        return (
            self.env.ref(
                f"account.{self.env.company.id}_tax_template_canon_sale_"
                f"{canon.split('.')[0]}",
                raise_if_not_found=False,
            )
            or self.env["account.tax"]
        )

    @api.model
    def _apply_taxes_to_price(
        self, price, currency, product_taxes, taxes, product_or_template, website=None
    ):
        # Include the digital canon in the displayed price, as it will be
        # charged on the order (l10n_es_digital_canon adds it as a line tax).
        taxes |= self._get_website_digital_canon_tax(
            product_or_template, website=website
        )
        return super()._apply_taxes_to_price(
            price, currency, product_taxes, taxes, product_or_template, website=website
        )
