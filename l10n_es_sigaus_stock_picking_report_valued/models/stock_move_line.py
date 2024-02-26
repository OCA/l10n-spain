# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    sigaus_amount_subtotal = fields.Monetary(
        compute="_compute_sigaus_amount", compute_sudo=True
    )
    sigaus_amount_tax = fields.Monetary(
        compute="_compute_sigaus_amount", compute_sudo=True
    )
    sigaus_amount_total = fields.Monetary(
        compute="_compute_sigaus_amount", compute_sudo=True
    )

    def _get_sigaus_product_taxes(self, sigaus_product):
        self.ensure_one()
        taxes = sigaus_product.taxes_id
        if not taxes:
            return False
        fiscal_position = self.sale_line.order_id.fiscal_position_id
        return fiscal_position.map_tax(taxes)

    def _get_sigaus_product_taxes_values(self, sigaus_product, price, qty):
        self.ensure_one()
        return self.env["account.tax"]._convert_to_tax_base_line_dict(
            self,
            partner=self.sale_line.order_partner_id,
            currency=self.currency_id,
            product=sigaus_product,
            taxes=self._get_sigaus_product_taxes(sigaus_product),
            price_unit=price,
            quantity=qty,
        )

    @api.depends("product_id", "date", "qty_done", "reserved_qty")
    def _compute_sigaus_amount(self):
        for line in self:
            subtotal = 0.0
            tax_amount = 0.0
            total = 0.0
            if (
                line.product_id
                and line.sale_line
                and line.sale_line.order_id.is_sigaus
                and line.product_id.sigaus_has_amount
            ):
                sigaus_product_id = self.env.ref(
                    "l10n_es_sigaus_account.aportacion_sigaus_product_template"
                )
                price = self.env["l10n.es.sigaus.amount"].get_sigaus_amount(
                    line.sale_line.order_id.date_order
                )
                quantity = line._get_report_valued_quantity()
                weight = quantity * line.product_id.weight
                tax_results = self.env["account.tax"]._compute_taxes(
                    [
                        line._get_sigaus_product_taxes_values(
                            sigaus_product_id, price, weight
                        )
                    ]
                )
                totals = list(tax_results["totals"].values())[0]
                subtotal = totals["amount_untaxed"]
                tax_amount = totals["amount_tax"]
                total = subtotal + tax_amount
            line.sigaus_amount_subtotal = subtotal
            line.sigaus_amount_tax = tax_amount
            line.sigaus_amount_total = total
