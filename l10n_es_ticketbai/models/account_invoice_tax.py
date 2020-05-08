# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.l10n_es_ticketbai_api.models.ticketbai_invoice import RefundType
from odoo.addons.l10n_es_ticketbai_api.models.ticketbai_invoice_tax import \
    NotSubjectToCause, TicketBaiTaxType
from odoo import models, fields, exceptions, _


class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    tbai_vat_exemption_key = fields.Many2one(
        comodel_name='tbai.vat.exemption.key', string='TicketBAI - VAT Exemption Key',
        copy=False)

    def tbai_get_amount_total_company(self):
        if self.invoice_id.currency_id.id != self.invoice_id.company_id.currency_id.id:
            currency = self.invoice_id.currency_id.with_context({
                'date': self.invoice_id.date or self.invoice_id.date_invoice,
                'company_id': self.invoice_id.company_id.id
            })
            amount_total = currency.compute(
                self.amount_total, self.invoice_id.company_id.currency_id)
        else:
            amount_total = self.amount_total
        return amount_total

    def tbai_get_associated_re_tax(self):
        re_invoice_tax = None
        s_iva_re_descriptions = self.env.ref(
            'l10n_es_ticketbai.tbai_tax_map_RE').tax_template_ids.mapped('description')
        lines = self.invoice_id.invoice_line_ids.filtered(
            lambda l: self.tax_id in l.invoice_line_tax_ids)
        re_taxes = lines.mapped('invoice_line_tax_ids').filtered(
            lambda tax: tax.description in s_iva_re_descriptions)
        if 1 < len(re_taxes):
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s Error: Tax %s contains multiple Equivalence "
                "Surcharge Taxes") % (self.invoice_id.number, self.tax_id.name))
        elif 1 == len(re_taxes):
            re_invoice_taxes = self.invoice_id.tax_line_ids.filtered(
                lambda invoice_tax: invoice_tax.tax_id.id == re_taxes.id)
            if 1 == len(re_invoice_taxes):
                re_invoice_tax = re_invoice_taxes
            else:
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s Error: the Invoice should have one tax line "
                    "for Tax %s") % (self.invoice_id.number, re_taxes.name))
        return re_invoice_tax

    def tbai_get_value_tax_type(self):
        if self.tbai_es_prestacion_servicios():
            res = TicketBaiTaxType.service.value
        elif self.tbai_es_entrega():
            res = TicketBaiTaxType.provision_of_goods.value
        else:
            res = None
        return res

    def tbai_es_prestacion_servicios(self):
        # No sujeto Repercutido (Servicios)
        descriptions = self.env.ref(
            'l10n_es_ticketbai.tbai_tax_map_SNS').tax_template_ids.mapped('description')
        # Prestación de servicios intracomunitario y extracomunitario
        descriptions += self.env.ref(
            'l10n_es_ticketbai.tbai_tax_map_SIE').tax_template_ids.mapped('description')
        # Servicios
        descriptions += self.env.ref(
            'l10n_es_ticketbai.tbai_tax_map_S').tax_template_ids.mapped('description')
        # Servicios Exento Repercutido
        descriptions += self.env.ref(
            'l10n_es_ticketbai.tbai_tax_map_SER').tax_template_ids.mapped('description')
        return self.tax_id.description in descriptions

    def tbai_es_entrega(self):
        # Bienes
        descriptions = self.env.ref(
            'l10n_es_ticketbai.tbai_tax_map_B').tax_template_ids.mapped('description')
        # No sujeto Repercutido (Bienes)
        descriptions += self.env.ref(
            'l10n_es_ticketbai.tbai_tax_map_BNS').tax_template_ids.mapped('description')
        # Entregas Intracomunitarias y Exportaciones exentas
        descriptions += self.env.ref(
            'l10n_es_ticketbai.tbai_tax_map_IEE').tax_template_ids.mapped('description')
        # Servicios Exento Repercutido
        descriptions += self.env.ref(
            'l10n_es_ticketbai.tbai_tax_map_SER').tax_template_ids.mapped('description')
        return self.tax_id.description in descriptions

    def tbai_get_value_causa(self):
        country_code = self.invoice_id.partner_id.tbai_get_partner_country_code()
        if country_code and self.env.ref('base.es').code.upper() == country_code:
            res = NotSubjectToCause.OT.value
        elif country_code:
            res = NotSubjectToCause.RL.value
        else:
            raise exceptions.ValidationError(_(
                "Country code for partner %s not found!"
            ) % self.invoice_id.partner_id.name)
        return res

    def tbai_get_value_base_imponible(self):
        if RefundType.differences.value == self.invoice_id.tbai_refund_type:
            sign = -1
        else:
            sign = 1
        if self.invoice_id.currency_id.id != self.invoice_id.company_id.currency_id.id:
            currency = self.invoice_id.currency_id.with_context({
                'date': self.invoice_id.date or self.invoice_id.date_invoice,
                'company_id': self.invoice_id.company_id.id
            })
            base = currency.compute(self.base, self.invoice_id.company_id.currency_id)
        else:
            base = self.base
        return "%.2f" % (sign * base)

    def tbai_get_value_tipo_no_exenta(self):
        isp_descriptions = self.env.ref(
            'l10n_es_ticketbai.tbai_tax_map_ISP').tax_template_ids.mapped('description')
        if self.tax_id.description in isp_descriptions:
            res = 'S2'
        else:
            res = 'S1'
        return res

    def tbai_get_value_cuota_impuesto(self):
        if RefundType.differences.value == self.invoice_id.tbai_refund_type:
            sign = -1
        else:
            sign = 1
        amount_total = self.tbai_get_amount_total_company()
        return "%.2f" % (sign * amount_total)

    def tbai_get_value_tipo_recargo_equivalencia(self):
        re_invoice_tax = self.tbai_get_associated_re_tax()
        if re_invoice_tax:
            res = "%.2f" % abs(re_invoice_tax.tax_id.amount)
        else:
            res = None
        return res

    def tbai_get_value_cuota_recargo_equivalencia(self):
        re_invoice_tax = self.tbai_get_associated_re_tax()
        if re_invoice_tax:
            amount_total = re_invoice_tax.tbai_get_amount_total_company()
            res = "%.2f" % amount_total
        else:
            res = None
        return res

    def tbai_get_value_op_recargo_equivalencia_o_reg_simplificado(self):
        re_invoice_tax = self.tbai_get_associated_re_tax()
        if re_invoice_tax or self.invoice_id.company_id.tbai_vat_regime_simplified:
            res = 'S'
        else:
            res = 'N'
        return res
