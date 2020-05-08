# -*- coding: utf-8 -*-
# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from enum import Enum
import logging
from datetime import datetime
from odoo import models, fields, exceptions, _, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class RefundTypeEnum(Enum):
    substitution = 'S'
    differences = 'I'


class RefundKeyEnum(Enum):
    R1 = 'R1'
    R2 = 'R2'
    R3 = 'R3'
    R4 = 'R4'


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    tbai_enabled = fields.Boolean(related='company_id.tbai_enabled', readonly=True)
    tbai_substitution_invoice_id = fields.Many2one(
        comodel_name='account.invoice', copy=False,
        help="Link between a validated Customer Invoice and its substitute.")
    tbai_previous_invoice_id = fields.Many2one(
        comodel_name='account.invoice', compute='_compute_tbai_previous_invoice', store=True)
    tbai_invoice_id = fields.Many2one(
        comodel_name='tbai.invoice.customer.invoice', string='TicketBai Invoice', copy=False)
    tbai_invoice_ids = fields.One2many(
        comodel_name='tbai.invoice.customer.invoice', inverse_name='invoice_id',
        string='TicketBai Invoices')
    tbai_cancellation_id = fields.Many2one(
        comodel_name='tbai.invoice.customer.cancellation', string='TicketBai Cancellation', copy=False)
    tbai_cancellation_ids = fields.One2many(
        comodel_name='tbai.invoice.customer.cancellation', inverse_name='invoice_id',
        string='TicketBai Cancellations')
    tbai_datetime_invoice = fields.Datetime(compute='_compute_tbai_datetime_invoice', store=True, copy=False)
    tbai_date_operation = fields.Datetime('Operation Date', copy=False)
    tbai_description_operation = fields.Text('Operation Description', default="/", copy=False)
    tbai_substitute_simplified_invoice = fields.Boolean('Substitute Simplified Invoice', copy=False)
    tbai_refund_key = fields.Selection(selection=[
        (RefundKeyEnum.R1.value, 'Art. 80.1, 80.2, 80.6 and rights founded error'),
        (RefundKeyEnum.R2.value, 'Art. 80.3'),
        (RefundKeyEnum.R3.value, 'Art. 80.4'),
        (RefundKeyEnum.R4.value, 'Art. 80 - other')
    ], help="BOE-A-1992-28740. Ley 37/1992, de 28 de diciembre, del Impuesto sobre el Valor Añadido. "
            "Artículo 80. Modificación de la base imponible.", copy=False)
    tbai_refund_type = fields.Selection(selection=[
        (RefundTypeEnum.substitution.value, 'By substitution'),
        (RefundTypeEnum.differences.value, 'By differences')
    ], copy=False)
    tbai_vat_regime_key = fields.Many2one(
        comodel_name='tbai.vat.regime.key', string='VAT Regime Key', copy=True)
    tbai_vat_regime_key2 = fields.Many2one(
        comodel_name='tbai.vat.regime.key', string='VAT Regime 2nd Key', copy=True)
    tbai_vat_regime_key3 = fields.Many2one(
        comodel_name='tbai.vat.regime.key', string='VAT Regime 3rd Key', copy=True)

    @api.multi
    @api.constrains('state')
    def _check_cancel_number_invoice(self):
        for record in self:
            if record.tbai_enabled and 'draft' == record.state and record.number:
                raise exceptions.ValidationError(_(
                    "Invoice %s. You cannot modify a numbered cancelled invoice!" % record.number))

    @api.model
    def create(self, vals):
        filter_refund = self._context.get('filter_refund', False)
        if filter_refund:
            if vals and vals.get('company_id', False) and vals.get('type', False):
                company = self.env['res.company'].browse(vals['company_id'])
                if company.tbai_enabled:
                    if not ('modify' == filter_refund and 'out_refund' == vals['type']):
                        if 'tbai_refund_type' not in vals:
                            if 'modify' == filter_refund:
                                vals['tbai_refund_type'] = RefundTypeEnum.substitution.value
                            elif filter_refund in ['refund', 'cancel'] and 'out_refund' == vals['type']:
                                vals['tbai_refund_type'] = RefundTypeEnum.differences.value
                        if 'tbai_refund_key' not in vals:
                            if not ('modify' == filter_refund and 'out_refund' == vals['type']):
                                vals['tbai_refund_key'] = RefundKeyEnum.R1.value
                        if 'fiscal_position_id' in vals:
                            fiscal_position = self.env['account.fiscal.position'].browse(vals['fiscal_position_id'])
                            if fiscal_position.tbai_vat_regime_key:
                                vals['tbai_vat_regime_key'] = fiscal_position.tbai_vat_regime_key.id
                            if fiscal_position.tbai_vat_regime_key2:
                                vals['tbai_vat_regime_key2'] = fiscal_position.tbai_vat_regime_key2.id
                            if fiscal_position.tbai_vat_regime_key3:
                                vals['tbai_vat_regime_key3'] = fiscal_position.tbai_vat_regime_key3.id
                    else:
                        vals['tbai_refund_type'] = False
                        vals['tbai_refund_key'] = False
                        vals['tbai_vat_regime_key'] = False
                        vals['tbai_vat_regime_key2'] = False
                        vals['tbai_vat_regime_key3'] = False
        return super().create(vals)

    @api.depends('date', 'date_invoice')
    def _compute_tbai_datetime_invoice(self):
        for record in self:
            record.tbai_datetime_invoice = fields.Datetime.now()

    @api.onchange('fiscal_position_id')
    def onchange_fiscal_position_id_tbai_vat_regime_key(self):
        self.tbai_vat_regime_key = self.fiscal_position_id.tbai_vat_regime_key.id
        self.tbai_vat_regime_key2 = self.fiscal_position_id.tbai_vat_regime_key2.id
        self.tbai_vat_regime_key3 = self.fiscal_position_id.tbai_vat_regime_key3.id

    @api.onchange('tbai_refund_type')
    def onchange_tbai_refund_type(self):
        if self.tbai_refund_type:
            if 'out_invoice' != self.type and RefundTypeEnum.substitution.value == self.tbai_refund_type:
                self.tbai_refund_type = False
                return {
                    'warning': {
                        'title': _("Warning"),
                        'message': _("TicketBai refund by substitution only available for Customer Invoices.")
                    }
                }
            elif 'out_refund' != self.type and RefundTypeEnum.differences.value == self.tbai_refund_type:
                self.tbai_refund_type = False
                return {
                    'warning': {
                        'title': _("Warning"),
                        'message': _("TicketBai refund by differences only available for Customer Credit Notes.")
                    }
                }

    @api.multi
    def _tbai_customer_invoice(self):
        for record in self:
            tbai_invoice = record.env['tbai.invoice.customer.invoice'].create({
                'invoice_id': record.id,
                'name': record._get_printed_report_name(),
                'company_id': record.company_id.id
            })
            tbai_invoice._build_tbai_invoice()
            record.tbai_invoice_id = tbai_invoice.id

    @api.multi
    def _tbai_invoice_cancel(self):
        for record in self:
            tbai_invoice = record.env['tbai.invoice.customer.cancellation'].create({
                'invoice_id': record.id,
                'name': "%s - %s" % (_("Cancellation"), record._get_printed_report_name()),
                'company_id': record.company_id.id
            })
            tbai_invoice._build_tbai_invoice()
            record.tbai_cancellation_id = tbai_invoice.id

    @api.multi
    def action_cancel(self):
        tbai_invoices = self.sudo().filtered(lambda x: x.tbai_enabled and 'open' == x.state)
        tbai_invoices._tbai_invoice_cancel()
        res = super().action_cancel()
        return res

    @api.multi
    def invoice_validate(self):
        res = super().invoice_validate()
        filter_refund = self._context.get('filter_refund', False)
        if not filter_refund or 'cancel' == filter_refund:
            # Do not send Credit Note to the Tax Agency when created from Refund Wizard in 'modify' mode.
            # Case 1. Filter refund -> refund: creates a draft credit note, not validated from wizard.
            # Case 2. Filter refund -> cancel: creates a validated credit note from wizard
            # Case 3. Filter refund -> modify: creates a validated credit note (do nothing) and a draft one.
            #   * In this last case, the draft credit note will be validated manually by the user. The already validated
            #   invoice cancels the one that is going to be substituted.
            # Filter refund invoices on which its refunded invoice does not have a TicketBai Invoice associated,
            # or does have associated a TicketBai cancellation.
            tbai_invoices = self.sudo().filtered(
                lambda x: x.tbai_enabled and (
                    'out_invoice' == x.type or
                    (
                        x.refund_invoice_id and 'out_refund' == x.type and
                        x.tbai_refund_type in [RefundTypeEnum.differences.value, RefundTypeEnum.substitution.value] and
                        x.refund_invoice_id.tbai_invoice_id and not x.refund_invoice_id.tbai_cancellation_id
                    )
                )
            )
            tbai_invoices._tbai_customer_invoice()
        return res

    @api.model
    def _get_refund_common_fields(self):
        fields = super()._get_refund_common_fields()
        fields.append('tbai_substitution_invoice_id')
        fields.append('company_id')  # TODO: PR to Odoo & OCA
        return fields

    def _prepare_tax_line_vals(self, line, tax):
        vals = super()._prepare_tax_line_vals(line, tax)
        if self.fiscal_position_id:
            exemption = self.fiscal_position_id.tbai_vat_exemption_ids.filtered(lambda e: e.tax_id.id == tax['id'])
            if 1 == len(exemption):
                vals['tbai_vat_exemption_key'] = exemption.tbai_vat_exemption_key.id
        return vals

    def tbai_get_previous_invoice_number(self):
        self.ensure_one()
        sequence = self.journal_id.invoice_sequence_id
        date = self.date or self.date_invoice
        prefix, suffix = sequence.with_context(ir_sequence_date=date, ir_sequence_date_range=date)._get_prefix_suffix()
        number_str = self.number
        if prefix and number_str and number_str.startswith(prefix):
            number_str = number_str[len(prefix):]
        if suffix and number_str and number_str.endswith(suffix):
            number_str = number_str[:-len(suffix)]
        if number_str and 1 < int(number_str):
            number = int(number_str) - 1
            res = "%s%d%s" % (prefix, number, suffix)
        else:
            res = None
        return res

    def tbai_is_invoice_refund(self):
        if 'out_refund' == self.type or (
                'out_invoice' == self.type and RefundTypeEnum.substitution.value == self.tbai_refund_type):
            res = True
        else:
            res = False
        return res

    @api.multi
    def _compute_tbai_previous_invoice(self):
        for record in self:
            previous_invoice_number = record.tbai_get_previous_invoice_number()
            res = False
            if previous_invoice_number:
                previous_invoice = self.search([('number', '=', previous_invoice_number)])
                if 1 == len(previous_invoice):
                    res = previous_invoice.id
            record.tbai_previous_invoice_id = res

    def tbai_get_context_records_Emisor(self):
        return self.company_id.partner_id

    def tbai_get_context_records_Destinatarios(self):
        return self.partner_id

    def tbai_get_context_records_CabeceraFactura(self):
        return self

    def tbai_get_context_records_FacturaRectificativa(self):
        return self.tbai_is_invoice_refund() and self or None

    def tbai_get_context_records_ImporteRectificacionSustitutiva(self):
        return RefundTypeEnum.substitution.value == self.tbai_refund_type and self.tbai_substitution_invoice_id or None

    def tbai_get_context_records_FacturasRectificadasSustituidas(self):
        return self.tbai_is_invoice_refund() and self or None

    def tbai_get_context_records_IDFacturaRectificadaSustituida(self):
        if RefundTypeEnum.substitution.value == self.tbai_refund_type:
            if self.tbai_substitution_invoice_id:
                invoice = self.tbai_substitution_invoice_id
            else:
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s Error: Substituted Invoice not found!") % self.number)
        else:
            invoice = self.refund_invoice_id
        return invoice

    def tbai_get_context_records_DatosFactura(self):
        return self

    def tbai_get_context_records_DetallesFactura(self):
        return self

    def tbai_get_context_records_IDDetalleFactura(self):
        return self.invoice_line_ids

    def tbai_get_context_records_Claves(self):
        return self

    def tbai_get_context_records_IDClave(self):
        return self.tbai_vat_regime_key + self.tbai_vat_regime_key2 + self.tbai_vat_regime_key3

    def tbai_get_context_records_TipoDesglose(self):
        """
        Instead of returning directly "self.tax_line_ids", return it inside a list to avoid iterating on method
        'build_complex_type'. We need "self.tax_line_ids" (RecordList) for "DesgloseFactura" or "DesgloseTipoOperacion".
        <element name="TipoDesglose" type="T:TipoDesgloseType"/>
            <sequence>
                <choice>
                    <element name="DesgloseFactura" type="T:DesgloseFacturaType"/>
                    <element name="DesgloseTipoOperacion" type="T:DesgloseTipoOperacionType"/>
                </choice>
            </sequence>
        """
        return [self.tax_line_ids]

    def tbai_get_context_records_EncadenamientoFacturaAnterior(self):
        if self.tbai_previous_invoice_id and self.tbai_previous_invoice_id.tbai_signature_value:
            res = self
        else:
            res = None
        return res

    def tbai_get_context_records_Software(self):
        return self.company_id

    def tbai_get_value_SerieFactura(self, max_length=20, **kwargs):
        """ V 1.1
        <element name="SerieFactura" type="T:TextMax20Type" minOccurs="0"/>
            <maxLength value="20"/>
        :return: Invoice Number Prefix
        """
        sequence = self.journal_id.invoice_sequence_id
        date = self.date or self.date_invoice
        prefix, suffix = sequence.with_context(ir_sequence_date=date, ir_sequence_date_range=date)._get_prefix_suffix()
        invoice_number_prefix = ''
        if prefix and max_length < len(prefix):
            # SerieFactura is not required.
            _logger.warning(_(
                "TicketBAI Invoice %s Error: Invoice Number Prefix longer than expected, %d characters max!"
            ) % (self.number, max_length))
        elif prefix and max_length >= len(prefix):
            invoice_number_prefix = prefix
        return invoice_number_prefix

    def tbai_get_value_NumFactura(self, max_length=20, **kwargs):
        """ V 1.1
        <element name="NumFactura" type="T:TextMax20Type"/>
            <maxLength value="20"/>
        :return: Invoice Number
        """
        invoice_number_prefix = self.tbai_get_value_SerieFactura()
        if invoice_number_prefix and not self.number.startswith(invoice_number_prefix):
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s Error: Invoice Number Prefix %s is not part of Invoice Number!"
            ) % (self.number, invoice_number_prefix))
        number = self.number[len(invoice_number_prefix):]
        if max_length < len(number):
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s Error: Invoice Number %s longer than expected, %d characters max!"
            ) % (self.number, number, max_length))
        return number

    def tbai_get_value_FechaExpedicionFactura(self, **kwargs):
        """ V 1.1
        <element name="FechaExpedicionFactura" type="T:FechaType"></element>
            <length value="10" />
            <pattern value="\d{2,2}-\d{2,2}-\d{4,4}"/>
        :return: Invoice Date
        """
        invoice_date = self.date or self.date_invoice
        date = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(invoice_date))
        return date.strftime("%d-%m-%Y")

    def tbai_get_value_HoraExpedicionFactura(self, **kwargs):
        """ V 1.1
        <element name="HoraExpedicionFactura" type="T:HoraType"/>
            <pattern value="\d{2,2}:\d{2,2}:\d{2,2}"/>
        :return: Invoice Time
        """
        invoice_datetime = self.tbai_datetime_invoice
        date = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(invoice_datetime))
        return date.strftime("%H:%M:%S")

    def tbai_get_value_FacturaEmitidaSustitucionSimplificada(self, **kwargs):
        """ V 1.1
        <element name="FacturaEmitidaSustitucionSimplificada" type="T:SiNoType" default="N"  minOccurs="0"/>
            <enumeration value="S"/>
            <enumeration value="N"/>
        :return: S or N (Y/Yes or N/No)
        """
        return 'N'

    def tbai_get_value_Codigo(self, **kwargs):
        """ V 1.1
        <element name="Codigo" type="T:ClaveTipoFacturaType"/>
            [
                <enumeration value="R1"></enumeration>
                ...
            ]
        :return: Invoice Refund Reason Code
        """
        return self.tbai_refund_key

    def tbai_get_value_Tipo(self, **kwargs):
        """ V 1.1
        <element name="Tipo" type="T:ClaveTipoRectificativaType"/>
            <enumeration value="S"/>
            <enumeration value="I"/>
        :return: S or I (Substitution or differences)
        """
        return self.tbai_refund_type

    def tbai_get_value_BaseRectificada(self, **kwargs):
        """ V 1.1
        <element name="BaseRectificada" type="T:ImporteSgn12.2Type"/>
            <pattern value="(\+|-)?\d{1,12}(\.\d{0,2})?"/>
        :return: Refund Invoice total untaxed amount
        """
        amount = abs(self.amount_untaxed_signed)
        return "%.2f" % amount

    def tbai_get_value_CuotaRectificada(self, **kwargs):
        """ V 1.1
        <element name="CuotaRectificada" type="T:ImporteSgn12.2Type"/>
            <pattern value="(\+|-)?\d{1,12}(\.\d{0,2})?"/>
        :return: Refund Invoice total tax amount
        """
        amount = abs(self.amount_total_company_signed - self.amount_untaxed_signed)
        return "%.2f" % amount

    def tbai_get_value_FechaOperacion(self, **kwargs):
        """ V 1.1
        <element name="FechaOperacion" type="T:FechaType" minOccurs="0"/>
            <length value="10" />
            <pattern value="\d{2,2}-\d{2,2}-\d{4,4}"/>
        :return: Operation Date
        """
        if self.tbai_date_operation:
            tbai_date_operation = datetime.strptime(
                self.tbai_date_operation, DEFAULT_SERVER_DATETIME_FORMAT).strftime("%d-%m-%Y")
            date_invoice = datetime.strptime(
                self.date or self.date_invoice, DEFAULT_SERVER_DATE_FORMAT).strftime("%d-%m-%Y")
            if tbai_date_operation == date_invoice:
                tbai_date_operation = None
        else:
            tbai_date_operation = None
        return tbai_date_operation

    def tbai_get_value_DescripcionFactura(self, **kwargs):
        """ V 1.1
        <element name="DescripcionFactura" type="T:TextMax250Type"/>
            <maxLength value="250"/>
        :return: Operation Description
        """
        return self.tbai_description_operation

    def tbai_get_value_ImporteTotalFactura(self, **kwargs):
        """ V 1.1
        <element name="ImporteTotalFactura" type="T:ImporteSgn12.2Type"/>
            <pattern value="(\+|-)?\d{1,12}(\.\d{0,2})?"/>
        :return: Invoice Total Amount
        """
        return "%.2f" % self.amount_total_company_signed

    def tbai_get_value_RetencionSoportada(self, **kwargs):
        """ V 1.1
        <element name="RetencionSoportada" type="T:ImporteSgn12.2Type" minOccurs="0"/>
            <pattern value="(\+|-)?\d{1,12}(\.\d{0,2})?"/>
        :return: Invoice Tax Retention Total Amount
        """
        irpf_descriptions = self.env.ref('l10n_es_ticketbai.tbai_tax_map_IRPF').tax_template_ids.mapped('description')
        taxes = self.tax_line_ids.filtered(lambda tax: tax.tax_id.description in irpf_descriptions)
        if 0 < len(taxes):
            res = "%.2f" % sum([tax.tbai_get_amount_total_company() for tax in taxes])
        else:
            res = None
        return res

    def tbai_get_value_SerieFacturaAnterior(self, max_length=None, **kwargs):
        """ V 1.1
        <element name="SerieFacturaAnterior" type="T:TextMax20Type" minOccurs="0"/>
            <maxLength value="20"/>
        :return: Previous Invoice Number Prefix
        """
        serie_factura = ''
        sequence = self.journal_id.invoice_sequence_id
        date = self.date or self.date_invoice
        prefix, suffix = sequence.with_context(
            ir_sequence_date=date, ir_sequence_date_range=date)._get_prefix_suffix()
        if prefix and max_length < len(prefix):
            # SerieFactura is not required.
            _logger.warning(_(
                "TicketBAI Invoice %s Error: Previous Invoice Number Prefix longer than expected, %d characters max!"
            ) % (self.number, max_length))
        elif prefix and max_length >= len(prefix):
            serie_factura = prefix
        return serie_factura

    def tbai_get_value_NumFacturaAnterior(self, max_length=None, **kwargs):
        """ V 1.1
        <element name="NumFacturaAnterior" type="T:TextMax20Type"/>
            <maxLength value="20"/>
        :return: Previous Invoice Number
        """
        previous_invoice_number = self.tbai_previous_invoice_id.number
        if max_length < len(previous_invoice_number):
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s Error: Previous Invoice Number longer than expected, %d characters max!"
            ) % (previous_invoice_number, max_length))
        # Invoice Number is not required in Odoo but, the TicketBAI Invoice is only created when an Odoo Invoice is
        # validated.
        return previous_invoice_number

    def tbai_get_value_FechaExpedicionFacturaAnterior(self, **kwargs):
        """ V 1.1
        <element name="FechaExpedicionFacturaAnterior" type="T:FechaType"/>
        <length value="10" />
            <pattern value="\d{2,2}-\d{2,2}-\d{4,4}"/>
        :return:
        """
        invoice_date = self.tbai_previous_invoice_id.date or self.tbai_previous_invoice_id.date_invoice
        date = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(invoice_date))
        return date.strftime("%d-%m-%Y")

    def tbai_get_value_SignatureValueFirmaFacturaAnterior(self, max_length=None, **kwargs):
        """ V 1.1
        <element name="SignatureValueFirmaFacturaAnterior" type="T:TextMax100Type"/>
            <maxLength value="100"/>
        """
        if self.self.tbai_previous_invoice_id:
            res = self.tbai_previous_invoice_id.tbai_signature[:max_length]
        else:
            res = None
        return res

    def tbai_get_value_NumSerieDispositivo(self, max_length=None, **kwargs):
        """ V 1.1
        <element name="NumSerieDispositivo" type="T:TextMax30Type" minOccurs="0"/>
            <maxLength value="30"/>
        :return: Device Serial Number
        """
        res = self.company_id.tbai_device_serial_number
        if res and max_length < len(res):
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s Error: Company Device Serial Number longer than expected, %d characters max!"
            ) % (self.number, max_length))
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    def tbai_get_value_DescripcionDetalle(self, **kwargs):
        """ V 1.1
        <element  name="DescripcionDetalle" type="T:TextMax250Type"/>
            <maxLength value="250"/>
        :return: Invoice Line Description
        """
        return self.name

    def tbai_get_value_Cantidad(self, **kwargs):
        """ V 1.1
        <element  name="Cantidad" type="T:ImporteSgn12.2Type"/>
            <pattern value="(\+|-)?\d{1,12}(\.\d{0,2})?"/>
        :return: Invoice Line Quantity
        """
        sign = -1 if RefundTypeEnum.differences.value == self.invoice_id.tbai_refund_type else 1
        return "%.2f" % (sign * self.quantity)

    def tbai_get_value_ImporteUnitario(self, **kwargs):
        """ V 1.1
        <element  name="ImporteUnitario" type="T:ImporteSgn12.2Type"/>
            <pattern value="(\+|-)?\d{1,12}(\.\d{0,2})?"/>
        :return: Invoice Line Price Unit
        """
        return "%.2f" % self.price_unit

    def tbai_get_value_Descuento(self, **kwargs):
        """ V 1.1
        <element  name="Descuento" type="T:ImporteSgn12.2Type" minOccurs="0"/>
            <pattern value="(\+|-)?\d{1,12}(\.\d{0,2})?"/>
        :return: Invoice Line Discount
        """
        if self.discount:
            res = "%.2f" % self.discount
        else:
            res = ''
        return res

    def tbai_get_value_ImporteTotal(self, **kwargs):
        """ V 1.1
        <element  name="ImporteTotal" type="T:ImporteSgn12.2Type"/>
            <pattern value="(\+|-)?\d{1,12}(\.\d{0,2})?"/>
        :return: Invoice Line Amount Total
        """
        return "%.2f" % self.price_subtotal_signed
