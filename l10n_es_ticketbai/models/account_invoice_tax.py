# -*- coding: utf-8 -*-
# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from .account_invoice import RefundTypeEnum
from odoo import models, fields, exceptions, _


class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    tbai_vat_exemption_key = fields.Many2one(
        comodel_name='tbai.vat.exemption.key', string='TicketBAI - VAT Exemption Key', copy=False)

    def tbai_get_amount_total_company(self):
        self.ensure_one()
        if self.invoice_id.currency_id.id != self.invoice_id.company_id.currency_id.id:
            currency = self.invoice_id.currency_id.with_context({
                'date': self.invoice_id.date or self.invoice_id.date_invoice,
                'company_id': self.invoice_id.company_id.id
            })
            amount_total = currency.compute(self.amount_total, self.invoice_id.company_id.currency_id)
        else:
            amount_total = self.amount_total
        return amount_total

    def tbai_get_associated_re_tax(self):
        re_invoice_tax = None
        s_iva_re_descriptions = self.env.ref('l10n_es_ticketbai.tbai_tax_map_RE').tax_template_ids.mapped('description')
        lines = self.invoice_id.invoice_line_ids.filtered(
            lambda l: self.tax_id in l.invoice_line_tax_ids)
        re_taxes = lines.mapped('invoice_line_tax_ids').filtered(lambda tax: tax.description in s_iva_re_descriptions)
        if 1 < len(re_taxes):
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s Error: Tax %s contains multiple Equivalence Surcharge Taxes") % (
                self.invoice_id.number, self.tax_id.name))
        elif 1 == len(re_taxes):
            re_invoice_taxes = self.invoice_id.tax_line_ids.filtered(
                lambda invoice_tax: invoice_tax.tax_id.id == re_taxes.id)
            if 1 == len(re_invoice_taxes):
                re_invoice_tax = re_invoice_taxes
            else:
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s Error: the Invoice should have one tax line for Tax %s") % (
                    self.invoice_id.number, re_taxes.name))
        return re_invoice_tax

    def tbai_get_context_records_DesgloseFactura(self):
        """
        Instead of returning directly "self", return it inside a list to avoid iterating on method
        'build_complex_type'. We need "self" (RecordList) for "Sujeta" and "NoSujeta".
        <element name="DesgloseFactura" type="T:DesgloseFacturaType"/>
            <sequence>
                <element name="Sujeta" type="T:SujetaType" minOccurs="0" />
                <element name="NoSujeta" type="T:NoSujetaType" minOccurs="0" />
            </sequence>
        """
        country_code = self[0].invoice_id.partner_id.tbai_get_partner_country_code()
        if country_code and self.env.ref('base.es').code.upper() == country_code:
            res = [self]
        else:
            res = None
        return res

    def tbai_get_context_records_DesgloseTipoOperacion(self):
        """
        Instead of returning directly "self", return it inside a list to avoid iterating on method
        'build_complex_type'. We need "self" (RecordList) for "PrestacionServicios" and "Entrega".
        <element name="DesgloseTipoOperacion" type="T:DesgloseTipoOperacionType"/>
            <sequence>
                <element name="PrestacionServicios" type="T:PrestacionServicios" minOccurs="0"/>
                <element name="Entrega" type="T:Entrega" minOccurs="0"/>
            </sequence>
        """
        country_code = self[0].invoice_id.partner_id.tbai_get_partner_country_code()
        if country_code and self.env.ref('base.es').code.upper() != country_code:
            res = [self]
        else:
            res = None
        return res

    def tbai_get_context_records_PrestacionServicios(self):
        """
        Instead of returning directly the filtered "self", return it inside a list to avoid iterating on method
        'build_complex_type'. We need the filtered "self" (RecordList) for "Sujeta" and "NoSujeta".
        <element name="PrestacionServicios" type="T:PrestacionServicios" minOccurs="0"/>
            <sequence>
                <element name="Sujeta" type="T:SujetaType" minOccurs="0" />
                <element name="NoSujeta" type="T:NoSujetaType" minOccurs="0" />
            </sequence>
        """
        # No sujeto Repercutido (Servicios)
        descriptions = self.env.ref('l10n_es_ticketbai.tbai_tax_map_SNS').tax_template_ids.mapped('description')
        # Prestación de servicios intracomunitario y extracomunitario
        descriptions += self.env.ref('l10n_es_ticketbai.tbai_tax_map_SIE').tax_template_ids.mapped('description')
        # Servicios
        descriptions += self.env.ref('l10n_es_ticketbai.tbai_tax_map_S').tax_template_ids.mapped('description')
        # Servicios Exento Repercutido
        descriptions += self.env.ref('l10n_es_ticketbai.tbai_tax_map_SER').tax_template_ids.mapped('description')
        return [self.filtered(lambda tax: tax.tax_id.description in descriptions)]

    def tbai_get_context_records_Entrega(self):
        """
        Instead of returning directly the filtered "self", return it inside a list to avoid iterating on method
        'build_complex_type'. We need the filtered "self" (RecordList) for "Sujeta" and "NoSujeta".
        <element name="Entrega" type="T:Entrega" minOccurs="0"/>
            <sequence>
                <element name="Sujeta" type="T:SujetaType" minOccurs="0" />
                <element name="NoSujeta" type="T:NoSujetaType" minOccurs="0" />
            </sequence>
        """
        # Bienes
        descriptions = self.env.ref('l10n_es_ticketbai.tbai_tax_map_B').tax_template_ids.mapped('description')
        # No sujeto Repercutido (Bienes)
        descriptions += self.env.ref('l10n_es_ticketbai.tbai_tax_map_BNS').tax_template_ids.mapped('description')
        # Entregas Intracomunitarias y Exportaciones exentas
        descriptions += self.env.ref('l10n_es_ticketbai.tbai_tax_map_IEE').tax_template_ids.mapped('description')
        # Servicios Exento Repercutido
        descriptions += self.env.ref('l10n_es_ticketbai.tbai_tax_map_SER').tax_template_ids.mapped('description')
        return [self.filtered(lambda tax: tax.tax_id.description in descriptions)]

    def tbai_get_context_records_Sujeta(self):
        """
        Instead of returning directly the filtered taxes, return it inside a list to avoid iterating on method
        'build_complex_type'. We need the filtered taxes (RecordList) for "Exenta" and "NoExenta".
        <element name="Sujeta" type="T:SujetaType" minOccurs="0" />
            <sequence>
                <element name="Exenta" type="T:ExentaType" minOccurs="0" />
                <element name="NoExenta" type="T:NoExentaType" minOccurs="0" />
            </sequence>
        """
        taxes = self.filtered(lambda tax: tax.tax_id.tbai_is_subject_to_tax())
        if 0 < len(taxes):
            res = [taxes]
        else:
            res = None
        return res

    def tbai_get_context_records_NoSujeta(self):
        """
        Instead of returning directly the filtered taxes, return it inside a list to avoid iterating on method
        'build_complex_type'. We need the filtered taxes (RecordList) for "DetalleNoSujeta".
        <element name="NoSujeta" type="T:NoSujetaType" minOccurs="0" />
            <sequence>
                <element name="DetalleNoSujeta" type="T:DetalleNoSujeta" minOccurs="1" maxOccurs="2" />
            </sequence>
        """
        taxes = self.filtered(lambda tax: not tax.tax_id.tbai_is_subject_to_tax())
        if 0 < len(taxes):
            res = [taxes]
        else:
            res = None
        return res

    def tbai_get_context_records_DetalleNoSujeta(self):
        return self

    def tbai_get_context_records_Exenta(self):
        """
        Instead of returning directly the filtered taxes, return it inside a list to avoid iterating on method
        'build_complex_type'. We need the filtered taxes (RecordList) for "DetalleExenta".
        <element name="Exenta" type="T:ExentaType" minOccurs="0" />
            <sequence>
                <element name="DetalleExenta" type="T:DetalleExentaType" minOccurs="1" maxOccurs="7" />
            </sequence>
        """
        taxes = self.filtered(lambda tax: tax.tax_id.tbai_is_tax_exempted())
        if 0 < len(taxes):
            res = [taxes]
        else:
            res = None
        return res

    def tbai_get_context_records_NoExenta(self):
        """
        Instead of returning directly the filtered taxes, return it inside a list to avoid iterating on method
        'build_complex_type'. We need the filtered taxes (RecordList) for "DetalleNoExenta".
        <element name="NoExenta" type="T:NoExentaType" minOccurs="0" />
            <sequence>
                <element name="DetalleNoExenta" type="T:DetalleNoExentaType" minOccurs="1" maxOccurs="2" />
            </sequence>
        """
        taxes = self.filtered(lambda tax: not tax.tax_id.tbai_is_tax_exempted())
        if 0 < len(taxes):
            res = [taxes]
        else:
            res = None
        return res

    def tbai_get_context_records_DetalleExenta(self):
        return self

    def tbai_get_context_records_DetalleNoExenta(self):
        """
        Instead of returning directly all filtered taxes, return its groups inside a list to avoid
        iterating on method 'build_complex_type'. We need to group the not exempted taxes in two groups,
        ISP and Not ISP, then for each group, we need the filtered taxes for "DesgloseIVA".
        <element name="DetalleNoExenta" type="T:DetalleNoExentaType" minOccurs="1" maxOccurs="2" />
            <sequence>
                <element name="TipoNoExenta" type="T:TipoOperacionSujetaNoExentaType"/>
                <element name="DesgloseIVA" type="T:DesgloseIVAType"/>
            </sequence>
        """
        isp_descriptions = self.env.ref('l10n_es_ticketbai.tbai_tax_map_ISP').tax_template_ids.mapped('description')
        not_exempted_taxes_isp = self.filtered(lambda tax: tax.tax_id.description in isp_descriptions)
        not_exempted_taxes_not_isp = self - not_exempted_taxes_isp
        return [not_exempted_taxes_isp, not_exempted_taxes_not_isp]

    def tbai_get_context_records_DesgloseIVA(self):
        """
        Instead of returning directly "self", return it inside a list to avoid iterating on method
        'build_complex_type'. We need "self" (RecordList) for "DetalleIVA".
        <element name="DesgloseIVA" type="T:DesgloseIVAType"/>
            <sequence>
                <element name="DetalleIVA" type="T:DetalleIVAType" maxOccurs="6" />
            </sequence>
        """
        return [self]

    def tbai_get_context_records_DetalleIVA(self):
        # Discard RecargoEquivalencia and IRPF Taxes
        descriptions = self.env.ref('l10n_es_ticketbai.tbai_tax_map_RE').tax_template_ids.mapped('description')
        descriptions += self.env.ref('l10n_es_ticketbai.tbai_tax_map_IRPF').tax_template_ids.mapped('description')
        return self.filtered(lambda tax: tax.tax_id.description not in descriptions)

    def tbai_get_value_Causa(self, **kwargs):
        """ V 1.1
        <element name="Causa" type="T:CausaNoSujetaType"/>
            <enumeration value="OT"></enumeration>
            <enumeration value="RL"></enumeration>
        :return: Not Subject to Tax Cause Code
        """
        country_code = self.invoice_id.partner_id.tbai_get_partner_country_code()
        if country_code and self.env.ref('base.es').code.upper() == country_code:
            res = 'OT'
        elif country_code:
            res = 'RL'
        else:
            res = None
        return res

    def tbai_get_value_Importe(self, **kwargs):
        """ V 1.1
        <element name="Importe" type="T:ImporteSgn12.2Type"/>
            <pattern value="(\+|-)?\d{1,12}(\.\d{0,2})?"/>
        :return: Tax Line Amount Total
        """
        amount_total = self.tbai_get_amount_total_company()
        return "%.2f" % amount_total

    def tbai_get_value_CausaExencion(self, **kwargs):
        """ V 1.1
        <element name="CausaExencion" type="T:CausaExencionType" />
            <enumeration value="E1"></enumeration>
            ...
        :return: Exemption Cause Code
        """
        return self.tbai_vat_exemption_key.code

    def tbai_get_value_BaseImponible(self, **kwargs):
        """ V 1.1
        <element name="BaseImponible" type="T:ImporteSgn12.2Type"/>
            <pattern value="(\+|-)?\d{1,12}(\.\d{0,2})?"/>
        :return: Tax Base Amount
        """
        sign = -1 if RefundTypeEnum.differences.value == self.invoice_id.tbai_refund_type else 1
        if self.invoice_id.currency_id.id != self.invoice_id.company_id.currency_id.id:
            currency = self.invoice_id.currency_id.with_context({
                'date': self.invoice_id.date or self.invoice_id.date_invoice,
                'company_id': self.invoice_id.company_id.id
            })
            base = currency.compute(self.base, self.invoice_id.company_id.currency_id)
        else:
            base = self.base
        return "%.2f" % (sign * base)

    def tbai_get_value_TipoNoExenta(self, **kwargs):
        """ V 1.1
        <element name="TipoNoExenta" type="T:TipoOperacionSujetaNoExentaType"/>
            <enumeration value="S1"></enumeration>
            <enumeration value="S2"></enumeration>
        :return: Not Exempted Tax Type Code
        """
        isp_descriptions = self.env.ref('l10n_es_ticketbai.tbai_tax_map_ISP').tax_template_ids.mapped('description')
        if all([record.tax_id.description in isp_descriptions for record in self]):
            res = 'S2'
        else:
            res = 'S1'
        return res

    def tbai_get_value_TipoImpositivo(self, **kwargs):
        """ V 1.1
        <element name="TipoImpositivo" type="T:Tipo3.2Type" minOccurs="0"/>
            <pattern value="\d{1,3}(\.\d{0,2})?"/>
        :return: Account Tax Amount (e.g.: 21% -> 21.0)
        """
        return "%.2f" % abs(self.tax_id.amount)

    def tbai_get_value_CuotaImpuesto(self, **kwargs):
        """ V 1.1
        <element name="CuotaImpuesto" type="T:ImporteSgn12.2Type" minOccurs="0" />
            <pattern value="(\+|-)?\d{1,12}(\.\d{0,2})?"/>
        :return: Tax Line Amount Total
        """
        sign = -1 if RefundTypeEnum.differences.value == self.invoice_id.tbai_refund_type else 1
        amount_total = self.tbai_get_amount_total_company()
        return "%.2f" % (sign * amount_total)

    def tbai_get_value_TipoRecargoEquivalencia(self, **kwargs):
        """ V 1.1
        <element name="TipoRecargoEquivalencia" type="T:Tipo3.2Type" minOccurs="0"/>
            <pattern value="\d{1,3}(\.\d{0,2})?"/>
        :return: Tax Line Equivalence Surcharge Account Tax Amount (e.g.: 1.4% -> 1.4)
        """
        re_invoice_tax = self.tbai_get_associated_re_tax()
        if re_invoice_tax:
            res = "%.2f" % abs(re_invoice_tax.tax_id.amount)
        else:
            res = None
        return res

    def tbai_get_value_CuotaRecargoEquivalencia(self, **kwargs):
        """ V 1.1
        <element name="CuotaRecargoEquivalencia" type="T:ImporteSgn12.2Type" minOccurs="0"/>
            <pattern value="(\+|-)?\d{1,12}(\.\d{0,2})?"/>
        :return: Tax Line Equivalence Surcharge Amount Total
        """
        re_invoice_tax = self.tbai_get_associated_re_tax()
        if re_invoice_tax:
            amount_total = re_invoice_tax.tbai_get_amount_total_company()
            res = "%.2f" % amount_total
        else:
            res = None
        return res

    def tbai_get_value_OperacionEnRecargoDeEquivalenciaORegimenSimplificado(self, **kwargs):
        """ V 1.1
        <element name="OperacionEnRecargoDeEquivalenciaORegimenSimplificado" type="T:SiNoType" minOccurs="0"/>
            <enumeration value="S"/>
            <enumeration value="N"/>
        :return: S/N (Y/Yes or N/No)
        """
        re_invoice_tax = self.tbai_get_associated_re_tax()
        if re_invoice_tax or self.invoice_id.company_id.tbai_vat_regime_simplified:
            res = 'S'
        else:
            res = 'N'
        return res
