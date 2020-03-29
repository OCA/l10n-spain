# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import OrderedDict
from .account_invoice import RefundTypeEnum
from odoo import models, fields, exceptions, _


class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    tbai_vat_exemption_key = fields.Many2one(
        comodel_name='tbai.vat.exemption.key', string='TicketBAI - VAT Exemption Key',
        copy=False)

    def tbai_get_amount_total_company(self):
        self.ensure_one()
        if self.invoice_id.currency_id.id != self.invoice_id.company_id.currency_id.id:
            currency = self.invoice_id.currency_id.with_context({
                'date': self.invoice_id.date or self.invoice_id.date_invoice,
                'company_id': self.invoice_id.company_id.id
            })
            amount_total = currency.compute(self.amount_total,
                                            self.invoice_id.company_id.currency_id)
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

    def tbai_build_prestacion_servicios(self):
        """ V 1.1
        <element name="PrestacionServicios" type="T:PrestacionServicios" minOccurs="0"/>
            <sequence>
                <element name="Sujeta" type="T:SujetaType" minOccurs="0" />
                <element name="NoSujeta" type="T:NoSujetaType" minOccurs="0" />
            </sequence>
        """
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
        taxes = self.filtered(lambda tax: tax.tax_id.description in descriptions)
        if taxes:
            res = OrderedDict({})
            sujeta = taxes.tbai_build_sujeta()
            if sujeta:
                res["Sujeta"] = sujeta
            no_sujeta = taxes.tbai_build_no_sujeta()
            if no_sujeta:
                res["NoSujeta"] = no_sujeta
        else:
            res = {}
        return res

    def tbai_build_entrega(self):
        """ V 1.1
        <element name="Entrega" type="T:Entrega" minOccurs="0"/>
            <sequence>
                <element name="Sujeta" type="T:SujetaType" minOccurs="0" />
                <element name="NoSujeta" type="T:NoSujetaType" minOccurs="0" />
            </sequence>
        """
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
        taxes = self.filtered(lambda tax: tax.tax_id.description in descriptions)
        if taxes:
            res = OrderedDict({})
            sujeta = taxes.tbai_build_sujeta()
            if sujeta:
                res["Sujeta"] = sujeta
            no_sujeta = taxes.tbai_build_no_sujeta()
            if no_sujeta:
                res["NoSujeta"] = no_sujeta
        else:
            res = {}
        return res

    def tbai_build_sujeta(self):
        """ V 1.1
        <element name="Sujeta" type="T:SujetaType" minOccurs="0" />
            <sequence>
                <element name="Exenta" type="T:ExentaType" minOccurs="0" />
                <element name="NoExenta" type="T:NoExentaType" minOccurs="0" />
            </sequence>
        """
        taxes = self.filtered(lambda tax: tax.tax_id.tbai_is_subject_to_tax())
        if 0 < len(taxes):
            res = OrderedDict({})
            exenta = taxes.tbai_build_exenta()
            if exenta:
                res["Exenta"] = exenta
            no_exenta = taxes.tbai_build_no_exenta()
            if no_exenta:
                res["NoExenta"] = no_exenta
        else:
            res = None
        return res

    def tbai_build_no_sujeta(self):
        """ V 1.1
        <element name="NoSujeta" type="T:NoSujetaType" minOccurs="0" />
            <sequence>
                <element name="DetalleNoSujeta" type="T:DetalleNoSujeta" minOccurs="1"
                maxOccurs="2" />
            </sequence>
        """
        taxes = self.filtered(lambda tax: not tax.tax_id.tbai_is_subject_to_tax())
        if 0 < len(taxes):
            res = {"DetalleNoSujeta": taxes.tbai_build_detalle_no_sujeta()}
        else:
            res = None
        return res

    def tbai_build_detalle_no_sujeta(self):
        """ V 1.1
        <element name="DetalleNoSujeta" type="T:DetalleNoSujeta" minOccurs="1"
        maxOccurs="2" />
        <sequence>
            <element name="Causa" type="T:CausaNoSujetaType"/>
            <element name="Importe" type="T:ImporteSgn12.2Type"/>
        </sequence>
        """
        if 2 < len(self):
            invoice_number = self[0].invoice_id.number
            raise exceptions.ValidationError(_(
                "Invoice %s should have maximum 2 not subject to tax groups!"
            ) % invoice_number)
        res = []
        for record in self:
            res.append(OrderedDict([
                ("Causa", record.tbai_get_value_causa()),
                ("Importe", record.tbai_get_value_importe())
            ]))
        return res

    def tbai_build_exenta(self):
        """
        <element name="Exenta" type="T:ExentaType" minOccurs="0" />
            <sequence>
                <element name="DetalleExenta" type="T:DetalleExentaType" minOccurs="1"
                maxOccurs="7" />
            </sequence>
        """
        taxes = self.filtered(lambda tax: tax.tax_id.tbai_is_tax_exempted())
        if 0 < len(taxes):
            res = {"DetalleExenta": taxes.tbai_build_detalle_exenta()}
        else:
            res = None
        return res

    def tbai_build_no_exenta(self):
        """
        <element name="NoExenta" type="T:NoExentaType" minOccurs="0" />
            <sequence>
                <element name="DetalleNoExenta" type="T:DetalleNoExentaType"
                minOccurs="1" maxOccurs="2" />
            </sequence>
        """
        taxes = self.filtered(lambda tax: not tax.tax_id.tbai_is_tax_exempted())
        if 0 < len(taxes):
            res = {"DetalleNoExenta": taxes.tbai_build_detalle_no_exenta()}
        else:
            res = None
        return res

    def tbai_build_detalle_exenta(self):
        """ V 1.1
        <element name="DetalleExenta" type="T:DetalleExentaType" minOccurs="1"
        maxOccurs="7" />
        <sequence>
            <element name="CausaExencion" type="T:CausaExencionType" />
            <element name="BaseImponible" type="T:ImporteSgn12.2Type"/>
        </sequence>
        """
        res = []
        if 7 < len(self):
            invoice_number = self[0].invoice_id.number
            raise exceptions.ValidationError(_(
                "Maximum number of exempted invoice tax lines for invoice %s is 7!"
            ) % invoice_number)
        for record in self:
            res.append(OrderedDict([
                ("CausaExencion", record.tbai_get_value_causa_exencion()),
                ("BaseImponible", record.tbai_get_value_base_imponible())
            ]))
        return res

    def tbai_build_detalle_no_exenta(self):
        """
        <element name="DetalleNoExenta" type="T:DetalleNoExentaType" minOccurs="1"
        maxOccurs="2" />
            <sequence>
                <element name="TipoNoExenta" type="T:TipoOperacionSujetaNoExentaType"/>
                <element name="DesgloseIVA" type="T:DesgloseIVAType"/>
            </sequence>
        """
        isp_descriptions = self.env.ref(
            'l10n_es_ticketbai.tbai_tax_map_ISP').tax_template_ids.mapped('description')
        not_exempted_taxes_isp = self.filtered(
            lambda tax: tax.tax_id.description in isp_descriptions)
        not_exempted_taxes_not_isp = self - not_exempted_taxes_isp
        res = []
        if 0 < len(not_exempted_taxes_isp):
            res.append(OrderedDict([
                ("TipoNoExenta",
                 not_exempted_taxes_isp.tbai_get_value_tipo_no_exenta()),
                ("DesgloseIVA", not_exempted_taxes_isp.tbai_build_desglose_iva())
            ]))
        if 0 < len(not_exempted_taxes_not_isp):
            res.append(OrderedDict([
                ("TipoNoExenta",
                    not_exempted_taxes_not_isp.tbai_get_value_tipo_no_exenta()),
                ("DesgloseIVA", not_exempted_taxes_not_isp.tbai_build_desglose_iva())
            ]))
        if not res:
            invoice_number = self[0].invoice_id.number
            raise exceptions.ValidationError(_(
                "Invoice %s should have at least one group of not exempted taxes!"
            ) % invoice_number)
        return res

    def tbai_build_desglose_iva(self):
        """
        <element name="DesgloseIVA" type="T:DesgloseIVAType"/>
            <sequence>
                <element name="DetalleIVA" type="T:DetalleIVAType" maxOccurs="6" />
            </sequence>
        """
        return {"DetalleIVA": self.tbai_build_detalle_iva()}

    def tbai_build_detalle_iva(self):
        # Discard RecargoEquivalencia and IRPF Taxes
        descriptions = self.env.ref(
            'l10n_es_ticketbai.tbai_tax_map_RE').tax_template_ids.mapped('description')
        descriptions += self.env.ref(
            'l10n_es_ticketbai.tbai_tax_map_IRPF').tax_template_ids.mapped(
            'description')
        taxes = self.filtered(lambda tax: tax.tax_id.description not in descriptions)
        if 6 < len(taxes):
            invoice_number = self[0].invoice_id.number
            raise exceptions.ValidationError(_(
                "Maximum number of invoice tax lines for invoice %s is 6!"
            ) % invoice_number)
        res = []
        # Comply with 88 line length OCA Travis
        func = \
            "tbai_get_value_operacion_en_recargo_de_equivalencia_o_regimen_simplificado"
        for record in taxes:
            record_res = OrderedDict([
                ("BaseImponible", record.tbai_get_value_base_imponible()),
                ("TipoImpositivo", record.tbai_get_value_tipo_impositivo()),
                ("CuotaImpuesto", record.tbai_get_value_cuota_impuesto())
            ])
            tipo_recargo_equivalencia = \
                record.tbai_get_value_tipo_recargo_equivalencia()
            if tipo_recargo_equivalencia:
                record_res["TipoRecargoEquivalencia"] = tipo_recargo_equivalencia
            cuota_recargo_equivalencia = \
                record.tbai_get_value_cuota_recargo_equivalencia()
            if cuota_recargo_equivalencia:
                record_res["CuotaRecargoEquivalencia"] = cuota_recargo_equivalencia
            record_res["OperacionEnRecargoDeEquivalenciaORegimenSimplificado"] = \
                getattr(record, func)()
            res.append(record_res)
        return res

    def tbai_get_value_causa(self):
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
            raise exceptions.ValidationError(_(
                "Country code for partner %s not found!"
            ) % self.invoice_id.partner_id.name)
        return res

    def tbai_get_value_importe(self):
        """ V 1.1
        <element name="Importe" type="T:ImporteSgn12.2Type"/>
            <pattern value="(\\+|-)?\\d{1,12}(\\.\\d{0,2})?"/>
        :return: Tax Line Amount Total
        """
        amount_total = self.tbai_get_amount_total_company()
        return "%.2f" % amount_total

    def tbai_get_value_causa_exencion(self):
        """ V 1.1
        <element name="CausaExencion" type="T:CausaExencionType" />
            <enumeration value="E1"></enumeration>
            ...
        :return: Exemption Cause Code
        """
        if not self.tbai_vat_exemption_key:
            invoice_number = self.invoice_id.number
            raise exceptions.ValidationError(_(
                "Invoice %s tax line %s should have exemption key!"
            ) % (invoice_number, self.name))
        return self.tbai_vat_exemption_key.code

    def tbai_get_value_base_imponible(self):
        """ V 1.1
        <element name="BaseImponible" type="T:ImporteSgn12.2Type"/>
            <pattern value="(\\+|-)?\\d{1,12}(\\.\\d{0,2})?"/>
        :return: Tax Base Amount
        """
        if RefundTypeEnum.differences.value == self.invoice_id.tbai_refund_type:
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
        """ V 1.1
        <element name="TipoNoExenta" type="T:TipoOperacionSujetaNoExentaType"/>
            <enumeration value="S1"></enumeration>
            <enumeration value="S2"></enumeration>
        :return: Not Exempted Tax Type Code
        """
        isp_descriptions = self.env.ref(
            'l10n_es_ticketbai.tbai_tax_map_ISP').tax_template_ids.mapped('description')
        if all([record.tax_id.description in isp_descriptions for record in self]):
            res = 'S2'
        else:
            res = 'S1'
        return res

    def tbai_get_value_tipo_impositivo(self):
        """ V 1.1
        <element name="TipoImpositivo" type="T:Tipo3.2Type" minOccurs="0"/>
            <pattern value="\\d{1,3}(\\.\\d{0,2})?"/>
        :return: Account Tax Amount (e.g.: 21% -> 21.0)
        """
        return "%.2f" % abs(self.tax_id.amount)

    def tbai_get_value_cuota_impuesto(self):
        """ V 1.1
        <element name="CuotaImpuesto" type="T:ImporteSgn12.2Type" minOccurs="0" />
            <pattern value="(\\+|-)?\\d{1,12}(\\.\\d{0,2})?"/>
        :return: Tax Line Amount Total
        """
        if RefundTypeEnum.differences.value == self.invoice_id.tbai_refund_type:
            sign = -1
        else:
            sign = 1
        amount_total = self.tbai_get_amount_total_company()
        return "%.2f" % (sign * amount_total)

    def tbai_get_value_tipo_recargo_equivalencia(self):
        """ V 1.1
        <element name="TipoRecargoEquivalencia" type="T:Tipo3.2Type" minOccurs="0"/>
            <pattern value="\\d{1,3}(\\.\\d{0,2})?"/>
        :return: Tax Line Equivalence Surcharge Account Tax Amount (e.g.: 1.4% -> 1.4)
        """
        re_invoice_tax = self.tbai_get_associated_re_tax()
        if re_invoice_tax:
            res = "%.2f" % abs(re_invoice_tax.tax_id.amount)
        else:
            res = None
        return res

    def tbai_get_value_cuota_recargo_equivalencia(self):
        """ V 1.1
        <element name="CuotaRecargoEquivalencia" type="T:ImporteSgn12.2Type"
        minOccurs="0"/>
            <pattern value="(\\+|-)?\\d{1,12}(\\.\\d{0,2})?"/>
        :return: Tax Line Equivalence Surcharge Amount Total
        """
        re_invoice_tax = self.tbai_get_associated_re_tax()
        if re_invoice_tax:
            amount_total = re_invoice_tax.tbai_get_amount_total_company()
            res = "%.2f" % amount_total
        else:
            res = None
        return res

    def tbai_get_value_operacion_en_recargo_de_equivalencia_o_regimen_simplificado(
            self):
        """ V 1.1
        <element name="OperacionEnRecargoDeEquivalenciaORegimenSimplificado"
        type="T:SiNoType" minOccurs="0"/>
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
