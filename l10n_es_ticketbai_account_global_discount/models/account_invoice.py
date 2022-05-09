# © 2022 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    def tbai_prepare_invoice_line_values(self):
        res = super().tbai_prepare_invoice_line_values()
        if self.global_discount_ids:
            for line in self.invoice_global_discount_ids:
                description_line = line.name[:250]
                if self.company_id.tbai_protected_data \
                        and self.company_id.tbai_protected_data_txt:
                    description_line = self.company_id.tbai_protected_data_txt[:250]
                res.append((0, 0, {
                    'description': description_line,
                    'quantity': '1.00',
                    'price_unit': "%.8f" % line.get_tbai_price_unit(),
                    'discount_amount': '0.00',
                    'amount_total': line.tbai_get_value_importe_total()
                }))
        return res


class AccountInvoiceGlobalDiscount(models.Model):
    _inherit = "account.invoice.global.discount"

    def get_tbai_price_unit(self):
        self.ensure_one()
        sign = 1
        if self.invoice_id.type in ('out_invoice', 'in_invoice'):
            sign = -1
        return self.discount_amount * sign

    def tbai_get_value_importe_total(self):
        self.ensure_one()
        tbai_maps = self.env["tbai.tax.map"].search([('code', '=', "IRPF")])
        irpf_taxes = self.env['l10n.es.aeat.report'].get_taxes_from_templates(
            tbai_maps.mapped("tax_template_ids")
        )
        currency = self.invoice_id and self.invoice_id.currency_id or None
        sign = 1
        if self.invoice_id.type in ('out_invoice', 'in_invoice'):
            sign = -1
        discount = sign * self.discount_amount
        taxes = (self.tax_ids - irpf_taxes).compute_all(
            discount, currency, 1,
            partner=self.invoice_id.partner_id)
        price_total = taxes['total_included'] if taxes else self.price_subtotal
        return "%.2f" % price_total
