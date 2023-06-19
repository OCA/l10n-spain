# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from datetime import datetime
from urllib.parse import urlencode
import io
import base64
from lxml import etree
from collections import OrderedDict
from .ticketbai_invoice_tax import TicketBaiTaxType, VATRegimeKey
from .ticketbai_response import TicketBaiResponseState, TicketBaiInvoiceResponseCode, \
    TicketBaiCancellationResponseCode
from .ticketbai_invoice_customer import TicketBaiCustomerIdType
from ..ticketbai.api import TicketBaiApi
from ..ticketbai.xml_schema import XMLSchema, TicketBaiSchema, \
    XMLSchemaModeNotSupported
from ..ticketbai.crc8 import crc8
from ..utils import utils as tbai_utils
from odoo import models, fields, exceptions, _, api

_logger = logging.getLogger(__name__)
TBAI_REJECTED_MAX_RETRIES = 5

try:
    import qrcode
except(ImportError, IOError) as err:
    _logger.error(err)


class TicketBaiQRParams(tbai_utils.EnumValues):
    tbai_identifier = 'id'
    invoice_number_prefix = 's'
    invoice_number = 'nf'
    invoice_total_amount = 'i'


class TicketBaiInvoiceState(tbai_utils.EnumValues):
    draft = 'draft'
    pending = 'pending'
    sent = 'sent'
    cancel = 'cancel'
    error = 'error'


class RefundType(tbai_utils.EnumValues):
    substitution = 'S'
    differences = 'I'


class RefundCode(tbai_utils.EnumValues):
    R1 = 'R1'
    R2 = 'R2'
    R3 = 'R3'
    R4 = 'R4'
    R5 = 'R5'


class SiNoType(tbai_utils.EnumValues):
    S = 'S'
    N = 'N'


class TicketBAIInvoice(models.Model):
    _name = 'tbai.invoice'
    _order = "id desc"
    _description = 'TicketBAI Invoices'

    @api.multi
    def send(self, **kwargs):
        self.ensure_one()
        error_msg = ''
        try:
            tbai_api = self.sudo().get_ticketbai_api()
        except exceptions.ValidationError as ve:
            _logger.exception(ve)
            tbai_api = None
            error_msg = ve.name
        if tbai_api is not None:
            response = tbai_api.requests_post(base64.decodebytes(self.datas))
            values = self.env['tbai.response'].prepare_tbai_response_values(
                response, **kwargs)
            values.update({
                'xml_fname': '_'.join([_('Response'), self.datas_fname])
            })
        else:
            values = self.env['tbai.response'].prepare_tbai_api_error_values(
                error_msg, **kwargs)
        values.update({
            'tbai_invoice_id': self.id
        })
        return self.env['tbai.response'].create(values)

    name = fields.Char(required=True)
    company_id = fields.Many2one(comodel_name='res.company', required=True)
    previous_tbai_invoice_id = fields.Many2one(comodel_name='tbai.invoice', copy=False)
    signature_value = fields.Char('Signature Value', default='', copy=False)
    tbai_identifier = fields.Char(
        'TBAI Identifier', compute='_compute_tbai_identifier', store=True, copy=False)
    tbai_customer_ids = fields.One2many(
        string='TicketBAI Invoice Recipients', copy=True,
        comodel_name='tbai.invoice.customer', inverse_name='tbai_invoice_id')
    tbai_response_ids = fields.One2many(
        comodel_name='tbai.response', inverse_name='tbai_invoice_id',
        string='Responses')
    tbai_invoice_line_ids = fields.One2many(
        string='TicketBAI Invoice Details', copy=True,
        comodel_name='tbai.invoice.line', inverse_name='tbai_invoice_id')
    tbai_tax_ids = fields.One2many(
        string='TicketBAI Invoice Taxes', copy=True,
        comodel_name='tbai.invoice.tax', inverse_name='tbai_invoice_id')
    tbai_invoice_refund_ids = fields.One2many(
        string='Refunded Invoices', copy=True,
        comodel_name='tbai.invoice.refund', inverse_name='tbai_invoice_id')
    qr_url = fields.Char('URL', compute='_compute_tbai_qr', store=True, copy=False)
    qr = fields.Binary(string="QR", compute='_compute_tbai_qr', store=True,
                       copy=False, attachment=True)
    datas = fields.Binary(copy=False, attachment=True)
    datas_fname = fields.Char('File Name', copy=False)
    file_size = fields.Integer('File Size', copy=False)
    state = fields.Selection(string='Status', selection=[
        (TicketBaiInvoiceState.draft.value, 'Draft'),
        (TicketBaiInvoiceState.pending.value, 'Pending'),
        (TicketBaiInvoiceState.sent.value, 'Sent'),
        (TicketBaiInvoiceState.cancel.value, 'Cancelled'),
        (TicketBaiInvoiceState.error.value, 'Error')
    ], default=TicketBaiInvoiceState.draft.value, required=True, index=True, copy=False)
    schema = fields.Selection(selection=[
        (TicketBaiSchema.TicketBai.value, 'TicketBai'),
        (TicketBaiSchema.AnulaTicketBai.value, 'AnulaTicketBai')
    ], required=True, help="""
    * TicketBai: Invoice
    * AnulaTicketBai: Invoice Cancellation
    """)
    api_url = fields.Char('TicketBAI API URL', compute='_compute_api_url')

    vat_regime_key = fields.Char('VAT Regime Key', default='')
    vat_regime_key2 = fields.Char('Second VAT Regime Key', default='')
    vat_regime_key3 = fields.Char('Third VAT Regime Key', default='')
    is_invoice_refund = fields.Boolean(
        help='TicketBAI Invoice is a refund (Substitution or Differences).')
    substituted_invoice_amount_total_untaxed = fields.Char(default='', help="""
    Original Invoice Total Amount without Taxes. E.g.:
    - Amount Total: 121.0 €
    - Tax Amount: 21 %
    - Total Tax Amount: 21 €
    * Amount Total Untaxed: 100 €
    """)
    substituted_invoice_total_tax_amount = fields.Char(default='', help="""
    Original Invoice Total Tax Amount. E.g.:
    - Amount Total: 121.0 €
    - Tax Amount: 21 %
    * Total Tax Amount: 21 €
    """)
    refund_code = fields.Selection(selection=[
        (RefundCode.R1.value, 'Art. 80.1, 80.2, 80.6 and rights founded error'),
        (RefundCode.R2.value, 'Art. 80.3'),
        (RefundCode.R3.value, 'Art. 80.4'),
        (RefundCode.R4.value, 'Art. 80 - other'),
        (RefundCode.R5.value, 'Simplified Invoice'),
    ], string='Invoice Refund Reason Code',
        help="BOE-A-1992-28740. Ley 37/1992, de 28 de diciembre, del Impuesto sobre el "
             "Valor Añadido. Artículo 80. Modificación de la base imponible.")
    refund_type = fields.Selection(selection=[
        (RefundType.substitution.value, 'S'),
        (RefundType.differences.value, 'I')
    ], help='Refund Invoice Type (S/Substitution or I/Differences).')
    description = fields.Char(default='/')
    simplified_invoice = fields.Selection(selection=[
        (SiNoType.S.value, 'S'),
        (SiNoType.N.value, 'N')
    ], help='S/Yes or N/No')
    substitutes_simplified_invoice = fields.Selection(selection=[
        (SiNoType.S.value, 'S'),
        (SiNoType.N.value, 'N')
    ], help='S/Yes or N/No')
    expedition_date = fields.Char(required=True)
    expedition_hour = fields.Char(default='')
    operation_date = fields.Char(default='')
    amount_total = fields.Char(default='')
    number = fields.Char(required=True)
    number_prefix = fields.Char(default='')
    tax_retention_amount_total = fields.Char(
        'Invoice Tax Retention Total Amount', default='')

    @api.multi
    @api.constrains('previous_tbai_invoice_id')
    def _check_previous_tbai_invoice_id(self):
        for r in self:
            if r.previous_tbai_invoice_id:
                if 1 < self.search_count([
                    ('previous_tbai_invoice_id', '=', r.previous_tbai_invoice_id.id),
                    ('state', 'in', [
                        TicketBaiInvoiceState.pending.value,
                        TicketBaiInvoiceState.sent.value])
                ]):
                    raise exceptions.ValidationError(_(
                        "TicketBAI Invoice %s:\n"
                        "Already exists a TicketBAI Invoice with the same link to its "
                        "previous TicketBAI Invoice.") % r.name)

    @api.multi
    @api.constrains('vat_regime_key')
    def _check_vat_regime_key(self):
        for record in self:
            if record.schema == TicketBaiSchema.TicketBai.value and \
                    (not record.vat_regime_key or record.vat_regime_key
                     not in VATRegimeKey.values()):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s: VAT Regime Key not valid.") % record.name)

    @api.multi
    @api.constrains('vat_regime_key2')
    def _check_vat_regime_key2(self):
        for record in self:
            if record.vat_regime_key2 and \
                    record.vat_regime_key2 not in VATRegimeKey.values():
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s: Second VAT Regime Key not valid."
                ) % record.name)

    @api.multi
    @api.constrains('vat_regime_key3')
    def _check_vat_regime_key3(self):
        for record in self:
            if record.vat_regime_key3 and \
                    record.vat_regime_key3 not in VATRegimeKey.values():
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s: Third VAT Regime Key not valid."
                ) % record.name)

    @api.multi
    @api.constrains('is_invoice_refund')
    def _check_is_invoice_refund(self):
        for record in self:
            if record.is_invoice_refund and (
                    not record.refund_code or not record.refund_type):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s: Refund Code and Type are required."
                ) % record.name)

    @api.multi
    @api.constrains('substituted_invoice_amount_total_untaxed')
    def _check_substituted_invoice_amount_total_untaxed(self):
        for record in self:
            if record.is_invoice_refund and \
                    record.refund_type == RefundType.substitution.value and \
                    not record.substituted_invoice_amount_total_untaxed:
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Substituted Invoice amount total untaxed is required."
                ) % record.name)
            elif record.substituted_invoice_amount_total_untaxed:
                tbai_utils.check_str_decimal(_(
                    "TicketBAI Invoice %s:\n"
                    "Substituted Invoice amount total untaxed"
                ) % record.name, record.substituted_invoice_amount_total_untaxed)

    @api.multi
    @api.constrains('substituted_invoice_total_tax_amount')
    def _check_substituted_invoice_total_tax_amount(self):
        for record in self:
            if record.is_invoice_refund and \
                    record.refund_type == RefundType.substitution.value and \
                    not record.substituted_invoice_total_tax_amount:
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Substituted Invoice Tax Amount Total is required."
                ) % record.name)
            elif record.substituted_invoice_total_tax_amount:
                tbai_utils.check_str_decimal(_(
                    "TicketBAI Invoice %s:\n"
                    "Substituted Invoice Tax Amount Total"
                ) % record.name, record.substituted_invoice_total_tax_amount)

    @api.multi
    @api.constrains('refund_code')
    def _check_refund_code(self):
        for record in self:
            if record.is_invoice_refund and not record.refund_code:
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Invoice Refund Reason Code is required."
                ) % record.name)

    @api.multi
    @api.constrains('description')
    def _check_description(self):
        for record in self:
            if record.schema == TicketBaiSchema.TicketBai.value and \
                    not record.description:
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Invoice Description is required.") % record.name)
            elif 250 < len(record.description):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Invoice description longer than expected. "
                    "Should be 250 characters max.!") % record.name)

    @api.multi
    @api.constrains('expedition_date')
    def _check_expedition_date(self):
        for record in self:
            tbai_utils.check_date(_(
                "TicketBAI Invoice %s: Expedition Date"
            ) % record.name, record.expedition_date)

    @api.multi
    @api.constrains('expedition_hour')
    def _check_expedition_hour(self):
        for record in self:
            if record.schema == TicketBaiSchema.TicketBai.value:
                tbai_utils.check_hour(_(
                    "TicketBAI Invoice %s: Expedition Hour"
                ) % record.name, record.expedition_hour)

    @api.multi
    @api.constrains('operation_date')
    def _check_operation_date(self):
        for record in self:
            if record.operation_date:
                tbai_utils.check_date(_(
                    "TicketBAI Invoice %s: Operation Date"
                ) % record.name, record.operation_date)

    @api.multi
    @api.constrains('amount_total')
    def _check_amount_total(self):
        for record in self:
            if record.schema == TicketBaiSchema.TicketBai.value:
                tbai_utils.check_str_decimal(_(
                    "TicketBAI Invoice %s: Amount Total"
                ) % record.name, record.amount_total)

    @api.multi
    @api.constrains('number')
    def _check_number(self):
        for record in self:
            if 20 < len(record.number):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Invoice Number longer than expected. "
                    "Should be 20 characters max.!") % record.name)

    @api.multi
    @api.constrains('number_prefix')
    def _check_number_prefix(self):
        for record in self:
            if record.number_prefix and 20 < len(record.number_prefix):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Invoice Number Prefix longer than expected. "
                    "Should be 20 characters max.!") % record.name)

    @api.multi
    @api.constrains('tax_retention_amount_total')
    def _check_tax_retention_amount_total(self):
        for record in self:
            if record.tax_retention_amount_total:
                tbai_utils.check_str_decimal(_(
                    "TicketBAI Invoice %s:\n"
                    "Invoice Tax Retention Total Amount"
                ) % record.name, record.tax_retention_amount_total)

    @api.multi
    @api.depends('signature_value')
    def _compute_tbai_identifier(self):
        for record in self:
            if record.signature_value:
                tbai_identifier_len_without_crc = 36
                tbai_identifier_len_with_crc = 39
                values = record._get_tbai_identifier_values()
                tbai_identifier_without_crc = '-'.join(values) + '-'
                if tbai_identifier_len_without_crc != len(tbai_identifier_without_crc):
                    raise exceptions.ValidationError(_(
                        "TicketBAI Invoice %s:\n"
                        "TBAI identifier without CRC-8 %s should be %d characters long!"
                    ) % (record.name, tbai_identifier_without_crc,
                         tbai_identifier_len_without_crc))
                crc = crc8(tbai_identifier_without_crc)
                values.append(crc)
                tbai_identifier_with_crc = '-'.join(values)
                if tbai_identifier_len_with_crc != len(tbai_identifier_with_crc):
                    raise exceptions.ValidationError(_(
                        "TicketBAI Invoice %s:\n"
                        "TBAI identifier %s should be %d characters long with CRC-8!"
                    ) % (record.name, tbai_identifier_with_crc,
                         tbai_identifier_len_with_crc))
                record.tbai_identifier = tbai_identifier_with_crc

    @api.multi
    @api.depends(
        'tbai_identifier',
        'company_id', 'company_id.tbai_tax_agency_id',
        'company_id.tbai_tax_agency_id.test_qr_base_url',
        'company_id.tbai_tax_agency_id.qr_base_url'
    )
    def _compute_tbai_qr(self):
        """ V 1.1
        Código QR TBAI, que consiste en un código con formato QR de tamaño mayor o igual
         a 30x30 milímetros y
        menor o igual a 40x40 milímetros (en adelante, QR TBAI).
        El nivel de corrección de errores del QR será M.
        La codificación utilizada para la generación del código será UTF-8.
        """
        for record in self:
            if record.tbai_identifier:
                if record.company_id.tbai_test_enabled:
                    qr_base_url = record.company_id.tbai_tax_agency_id.test_qr_base_url
                else:
                    qr_base_url = record.company_id.tbai_tax_agency_id.qr_base_url
                qr_values = record._get_qr_url_values()
                qr_url_without_crc = "%s?%s" % (
                    qr_base_url, urlencode(qr_values, encoding='utf-8'))
                qr_crc = crc8(qr_url_without_crc)
                qr_values['cr'] = qr_crc
                qr_url_with_crc = "%s?%s" % (
                    qr_base_url, urlencode(qr_values, encoding='utf-8'))
                record.qr_url = qr_url_with_crc
                # Let QRCode decide the best version when calling make()
                qr = qrcode.QRCode(
                    border=0, error_correction=qrcode.constants.ERROR_CORRECT_M)
                qr.add_data(record.qr_url)
                qr.make()
                img = qr.make_image()
                with io.BytesIO() as temp:
                    img.save(temp, format="PNG")
                    record.qr = base64.b64encode(temp.getvalue())

    @api.multi
    @api.depends(
        'company_id', 'company_id.tbai_tax_agency_id',
        'company_id.tbai_tax_agency_id.rest_url_invoice',
        'company_id.tbai_tax_agency_id.test_rest_url_invoice',
        'company_id.tbai_tax_agency_id.rest_url_cancellation',
        'company_id.tbai_tax_agency_id.test_rest_url_cancellation'
    )
    def _compute_api_url(self):
        for record in self:
            if record.schema == TicketBaiSchema.TicketBai.value:
                if record.company_id.tbai_test_enabled:
                    url = record.company_id.tbai_tax_agency_id.\
                        test_rest_url_invoice
                else:
                    url = record.company_id.tbai_tax_agency_id.rest_url_invoice
            elif record.schema == TicketBaiSchema.AnulaTicketBai.value:
                if record.company_id.tbai_test_enabled:
                    url = record.company_id.tbai_tax_agency_id.\
                        test_rest_url_cancellation
                else:
                    url = record.company_id.tbai_tax_agency_id.rest_url_cancellation
            else:
                raise XMLSchemaModeNotSupported(_(
                    "TicketBAI Invoice %s: XML Invoice schema not supported!"
                ) % record.name)
            record.api_url = url

    @api.multi
    def get_ticketbai_api(self, **kwargs):
        self.ensure_one()
        p12_buffer = self.company_id.tbai_certificate_get_p12_buffer()
        password = self.company_id.tbai_certificate_get_p12_password()
        return TicketBaiApi(
            self.api_url, p12_buffer=p12_buffer, password=password, **kwargs)

    @api.model
    def get_next_pending_invoice(self, company_id=False, limit=1):
        domain = [
            ('state', '=', TicketBaiInvoiceState.pending.value)
        ]
        if company_id:
            domain.append(('company_id', '=', company_id))
        return self.search(domain, order='id ASC', limit=limit)

    @api.multi
    def error(self):
        self.write({'state': TicketBaiInvoiceState.error.value})

    @api.multi
    def cancel(self):
        self.write({'state': TicketBaiInvoiceState.cancel.value})

    @api.multi
    def mark_as_sent(self):
        self.write({'state': TicketBaiInvoiceState.sent.value})

    @api.multi
    def mark_as_pending(self):
        self.write({'state': TicketBaiInvoiceState.pending.value})

    def get_exempted_taxes(self):
        """
        * Subject to:
          - Exempted
        :return: Recordset of tbai.invoice.tax
        """
        return self.get_subject_to_taxes().filtered(lambda x: x.is_exempted)

    def get_not_exempted_taxes(self):
        """
        * Subject to:
          - Not exempted
        :return: Recordset of tbai.invoice.tax
        """
        return self.get_subject_to_taxes().filtered(lambda x: not x.is_exempted)

    def get_subject_to_taxes(self):
        """
        * Subject to
        :return: Recordset of tbai.invoice.tax
        """
        return self.get_taxes().filtered(lambda x: x.is_subject_to)

    def get_not_subject_to_taxes(self):
        """
        * Not subject to
        :return: Recordset of tbai.invoice.tax
        """
        return self.get_taxes().filtered(lambda x: not x.is_subject_to)

    def get_taxes(self):
        """ Filter TicketBai Taxes when Customer is not from Spain.
        * DesgloseTipoOperacion
          - PrestacionServicios
          - Entrega
        :return: Recordset of tbai.invoice.tax
        """
        tax_type = self._context.get('tbai_tax_type', False)
        if tax_type:
            taxes = self.tbai_tax_ids.filtered(lambda x: x.type == tax_type)
        else:
            taxes = self.tbai_tax_ids
        return taxes

    @api.model
    def mark_chain_as_error(self, invoice_to_error):
        # Restore last invoice successfully sent
        if TicketBaiSchema.TicketBai.value == invoice_to_error.schema:
            invoice_to_error.company_id.tbai_last_invoice_id = \
                invoice_to_error.previous_tbai_invoice_id
        while invoice_to_error:
            invoice_to_error.error()
            invoice_to_error = self.search([
                ('previous_tbai_invoice_id', '=', invoice_to_error.id)
            ])

    @api.model
    def send_pending_invoices(self):
        next_pending_invoice = self.get_next_pending_invoice()
        retry_later = False
        rejected_retries = 0
        while next_pending_invoice and not retry_later and \
                rejected_retries < TBAI_REJECTED_MAX_RETRIES:
            try:
                with self.env.cr.savepoint():
                    tbai_response = next_pending_invoice.send()
                    if TicketBaiResponseState.RECEIVED.value == \
                            tbai_response.state:
                        next_pending_invoice.mark_as_sent()
                    elif TicketBaiResponseState.REJECTED.value \
                            == tbai_response.state:
                        # Reestablish the company pointer to the last invoice built and
                        # successfully sent.
                        # Mark pending invoices as error, except in the following:
                        # - TicketBai (Invoice)
                        #   - 005: Invoice already registered -> mark as sent.
                        #   - 006: service not available. Retry later.
                        # - AnulaTicketBai (Cancellation)
                        #   - 011: Invoice already registered -> mark as sent.
                        #   - 012: service not available. Retry later.
                        error = True
                        # TicketBAI Response warning and error codes
                        response_codes = list(set(
                            tbai_response.tbai_response_message_ids
                            .mapped('code')))
                        if TicketBaiSchema.TicketBai.value ==\
                                next_pending_invoice.schema:
                            if TicketBaiInvoiceResponseCode.\
                                    INVOICE_ALREADY_REGISTERED.value \
                                    in response_codes:
                                next_pending_invoice.mark_as_sent()
                                error = False
                            elif TicketBaiInvoiceResponseCode.\
                                    SERVICE_NOT_AVAILABLE.value \
                                    in response_codes:
                                retry_later = True
                                error = False
                        elif TicketBaiSchema.AnulaTicketBai.value == \
                                next_pending_invoice.schema:
                            if TicketBaiCancellationResponseCode.\
                                    INVOICE_ALREADY_CANCELLED.value \
                                    in response_codes:
                                next_pending_invoice.mark_as_sent()
                                error = False
                            elif TicketBaiCancellationResponseCode.\
                                    SERVICE_NOT_AVAILABLE.value \
                                    in response_codes:
                                retry_later = True
                                error = False
                        if error:
                            self.mark_chain_as_error(next_pending_invoice)
                            rejected_retries += 1
                    elif TicketBaiResponseState.REQUEST_ERROR.value == \
                            tbai_response.state:
                        # In case of multi-company it would be delaying
                        # independently from the company and tax agency,
                        # maybe only one of them is out of service.
                        # For now delay for all companies and all tax agencies.
                        retry_later = True
                    elif TicketBaiResponseState.BUILD_ERROR.value == \
                            tbai_response.state:
                        retry_later = True
                    if not retry_later:
                        next_pending_invoice = self.get_next_pending_invoice()
            except Exception:
                _logger.exception('Communication failed with TicketBAI server.',
                                  exc_info=True)
                retry_later = True

    def _get_tbai_identifier_values(self):
        """ V 1.2
        TBAI-<vat_number>-<invoice_date>-<signature_value>
        :return: list<str>
        """
        expedition_date = datetime.strptime(
            self.expedition_date, '%d-%m-%Y').strftime('%d%m%y')
        nif = self.company_id.partner_id.tbai_get_value_nif()
        if not nif:
            raise exceptions.ValidationError(_(
                "The Company %s VAT Number is required.") % self.company_id.name)
        return [
            'TBAI', nif, expedition_date, self.signature_value[:13]]

    def _get_qr_url_values(self):
        """ V 1.2
        <base_url>?id=<tbai_identifier>&s=<invoice_number_prefix>&nf=<invoice_number>
        &i=<invoice_total_amount>&cr=<crc8>
        :return: OrderedDict
        """
        res = OrderedDict([
            (TicketBaiQRParams.tbai_identifier.value, self.tbai_identifier),
        ])
        res[TicketBaiQRParams.invoice_number_prefix.value] = self.number_prefix or ""
        res[TicketBaiQRParams.invoice_number.value] = self.number
        res[TicketBaiQRParams.invoice_total_amount.value] = self.amount_total
        return res

    def build_cancellation(self):
        return {"AnulaTicketBai": OrderedDict([
            ("Cabecera", self.build_cabecera()),
            ("IDFactura", self.build_id_factura()),
            ("HuellaTBAI", self.build_huella_tbai()),
        ])}

    def build_invoice(self):
        return {"TicketBai": OrderedDict([
            ("Cabecera", self.build_cabecera()),
            ("Sujetos", self.build_sujetos()),
            ("Factura", self.build_factura()),
            ("HuellaTBAI", self.build_huella_tbai()),
        ])}

    def get_tbai_xml_unsigned(self):
        if self.schema == TicketBaiSchema.TicketBai.value:
            my_ordered_dict = self.build_invoice()
        elif self.schema == TicketBaiSchema.AnulaTicketBai.value:
            my_ordered_dict = self.build_cancellation()
        else:
            raise XMLSchemaModeNotSupported(_(
                "TicketBAI Invoice %s: XML schema not supported!"
            ) % self.name)
        return XMLSchema(self.schema).dict2xml(my_ordered_dict)

    def get_tbai_xml_signed_and_signature_value(self):
        root = self.get_tbai_xml_unsigned()
        p12 = self.company_id.tbai_certificate_get_p12()
        tax_agency = self.company_id.tbai_tax_agency_id
        signature_value = XMLSchema.sign(root, p12, tax_agency)
        return root, signature_value

    def build_tbai_invoice(self):
        self.ensure_one()
        if self.schema == TicketBaiSchema.TicketBai.value:
            self.previous_tbai_invoice_id = self.company_id.tbai_last_invoice_id
        root, signature_value = self.get_tbai_xml_signed_and_signature_value()
        root_str = etree.tostring(root, xml_declaration=True, encoding='utf-8')
        self.datas = base64.b64encode(root_str)
        self.datas_fname = "%s.xsig" % self.name.replace('/', '-')
        self.file_size = len(self.datas)
        self.signature_value = signature_value
        self.mark_as_pending()
        if self.schema == TicketBaiSchema.TicketBai.value:
            self.company_id.tbai_last_invoice_id = self

    def build_cabecera(self):
        """ V 1.2
        Get TicketBAI version from the Company Tax Agency.

        <element name="Cabecera" type="T:Cabecera"/>
        <complexType name="Cabecera">
            <sequence>
                <element name="IDVersionTBAI" type="T:IDVersionTicketBaiType"/>
                    <enumeration value="1.2"/>
            </sequence>
        </complexType>
        :return: Tax Agency
        """
        return {"IDVersionTBAI": self.company_id.tbai_tax_agency_id.version}

    def build_cabecera_factura(self):
        res = OrderedDict([
            ("SerieFactura", self.number_prefix),
            ("NumFactura", self.number),
            ("FechaExpedicionFactura", self.expedition_date),
            ("HoraExpedicionFactura", self.expedition_hour)
        ])
        if self.simplified_invoice:
            res["FacturaSimplificada"] = self.simplified_invoice
        if self.substitutes_simplified_invoice:
            res["FacturaEmitidaSustitucionSimplificada"] = \
                self.substitutes_simplified_invoice
        factura_rectificativa = self.build_factura_rectificativa()
        if factura_rectificativa:
            res["FacturaRectificativa"] = factura_rectificativa
        facturas_rectificadas_sustituidas = \
            self.build_facturas_rectificadas_sustituidas()
        if facturas_rectificadas_sustituidas:
            res["FacturasRectificadasSustituidas"] = facturas_rectificadas_sustituidas
        return res

    def build_claves(self):
        """ V 1.2
        The specification document indicates that at least 1 regime key is required.
        <element name="IDClave" type="T:IDClaveType" maxOccurs="3"/>
        <sequence>
            <element  name="ClaveRegimenIvaOpTrascendencia"
                      type="T:IdOperacionesTrascendenciaTributariaType"/>
        </sequence>
        :return: dict
        """
        res = {"IDClave": []}
        res["IDClave"].append({"ClaveRegimenIvaOpTrascendencia": self.vat_regime_key})
        if self.vat_regime_key2:
            res["IDClave"].append(
                {"ClaveRegimenIvaOpTrascendencia": self.vat_regime_key2})
        if self.vat_regime_key3:
            res["IDClave"].append(
                {"ClaveRegimenIvaOpTrascendencia": self.vat_regime_key3})
        return res

    def build_datos_factura(self):
        res = OrderedDict()
        if self.operation_date:
            res["FechaOperacion"] = self.operation_date
        res["DescripcionFactura"] = self.description
        detalles_factura = self.build_detalles_factura()
        if detalles_factura:
            res["DetallesFactura"] = detalles_factura
        if self.tax_retention_amount_total:
            res["ImporteTotalFactura"] = "%.2f" % (
                float(self.amount_total) + float(self.tax_retention_amount_total)
            )
            res["RetencionSoportada"] = self.tax_retention_amount_total
        else:
            res["ImporteTotalFactura"] = self.amount_total
        res["Claves"] = self.build_claves()
        return res

    def build_destinatarios(self):
        """Support only for one customer."""
        gipuzkoa_tax_agency = self.env.ref(
            "l10n_es_ticketbai_api.tbai_tax_agency_gipuzkoa")
        araba_tax_agency = self.env.ref(
            "l10n_es_ticketbai_api.tbai_tax_agency_araba")
        tax_agency = self.company_id.tbai_tax_agency_id
        res = []
        if 100 < len(self.tbai_customer_ids):
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s:\n"
                "Maximum 100 recipients allowed for each Invoice!"
            ) % self.name)
        for customer in self.tbai_customer_ids:
            customer_res = OrderedDict()
            if customer.nif:
                customer_res["NIF"] = customer.nif
            elif customer.idtype and customer.identification_number:
                customer_res["IDOtro"] = OrderedDict()
                if (
                    customer.country_code and
                    customer.idtype != TicketBaiCustomerIdType.T02.value
                ):
                    customer_res["IDOtro"]["CodigoPais"] = customer.country_code
                customer_res["IDOtro"]["IDType"] = customer.idtype
                customer_res["IDOtro"]["ID"] = customer.identification_number
            customer_res["ApellidosNombreRazonSocial"] = customer.name
            if customer.zip:
                customer_res["CodigoPostal"] = customer.zip
            elif tax_agency in (gipuzkoa_tax_agency, araba_tax_agency):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "ZIP code for %s is required for the Tax Agency %s!"
                ) % (self.name, customer.name, tax_agency.name))
            if customer.address:
                customer_res["Direccion"] = customer.address
            elif tax_agency in (gipuzkoa_tax_agency, araba_tax_agency):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Address for %s is required for the Tax Agency %s!"
                ) % (self.name, customer.name, tax_agency.name))
            if ('NIF' in customer_res or 'IDOtro' in customer_res) and \
                    'ApellidosNombreRazonSocial' in customer_res:
                res.append(OrderedDict({"IDDestinatario": customer_res}))
        return res

    def build_detalle_exenta(self):
        """ V 1.2
        <element name="DetalleExenta" type="T:DetalleExentaType" minOccurs="1"
                 maxOccurs="7" />
            <sequence>
                <element name="CausaExencion" type="T:CausaExencionType" />
                    <restriction base="string">
                        <enumeration value="E1">
                        ...
                <element name="BaseImponible" type="T:ImporteSgn12.2Type"/>
            </sequence>
        :return: list<OrderedDict>
        """
        tbai_exempted_taxes = self.get_exempted_taxes()
        res = []
        if 7 < len(tbai_exempted_taxes):
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s: Max. number of exempted taxes is 7!"
            ) % self.name)
        for tax in tbai_exempted_taxes:
            res.append(OrderedDict([
                ("CausaExencion", tax.exempted_cause),
                ("BaseImponible", tax.base)
            ]))
        return res

    def build_detalle_no_exenta(self):
        """ V 1.2
        1. Inversión del Sujeto Pasivo (ISP) taxes (tax is paid by the customer).
        2. Other taxes
        <element name="DetalleNoExenta" type="T:DetalleNoExentaType" minOccurs="1"
                 maxOccurs="2" />
            <sequence>
                <element name="TipoNoExenta" type="T:TipoOperacionSujetaNoExentaType"/>
                    <restriction base="string">
                        <enumeration value="S1">
                        <enumeration value="S2">
                <element name="DesgloseIVA" type="T:DesgloseIVAType"/>
                    <element name="DetalleIVA" type="T:DetalleIVAType" maxOccurs="6" />
                        <sequence>
                            <element name="BaseImponible" type="T:ImporteSgn12.2Type"/>
                            <element name="TipoImpositivo" type="T:Tipo3.2Type"
                                     minOccurs="0"/>
                            <element name="CuotaImpuesto" type="T:ImporteSgn12.2Type"
                                     minOccurs="0" />
                            <element name="TipoRecargoEquivalencia" type="T:Tipo3.2Type"
                                     minOccurs="0"/>
                            <element name="CuotaRecargoEquivalencia"
                                     type="T:ImporteSgn12.2Type" minOccurs="0"/>
                            <element
                            name="OperacionEnRecargoDeEquivalenciaORegimenSimplificado"
                            type="T:SiNoType" minOccurs="0"/>
        :return: list<OrderedDict>
        """
        not_exempted_taxes = self.get_not_exempted_taxes()
        res = []
        not_exempted_taxes_isp = OrderedDict()
        not_exempted_taxes_not_isp = OrderedDict()
        for tax in not_exempted_taxes:
            tax_details = OrderedDict([
                ("BaseImponible", tax.base),
                ("TipoImpositivo", tax.amount),
                ("CuotaImpuesto", tax.amount_total)
            ])
            if tax.re_amount and tax.re_amount_total:
                tax_details["TipoRecargoEquivalencia"] = tax.re_amount
                tax_details["CuotaRecargoEquivalencia"] = tax.re_amount_total
            if tax.surcharge_or_simplified_regime:
                tax_details[
                    "OperacionEnRecargoDeEquivalenciaORegimenSimplificado"] = \
                    tax.surcharge_or_simplified_regime
            if tax.not_exempted_type == "S1":
                not_exempted_taxes_not_isp.setdefault("TipoNoExenta", "S1")
                not_exempted_taxes_not_isp.setdefault("DesgloseIVA", {"DetalleIVA": []})
                not_exempted_taxes_not_isp["DesgloseIVA"]["DetalleIVA"].append(
                    tax_details
                )
            elif tax.not_exempted_type == "S2":
                not_exempted_taxes_isp.setdefault("TipoNoExenta", "S2")
                not_exempted_taxes_isp.setdefault("DesgloseIVA", {"DetalleIVA": []})
                not_exempted_taxes_isp["DesgloseIVA"]["DetalleIVA"].append(
                    tax_details
                )
        if not_exempted_taxes_isp:
            res.append(not_exempted_taxes_isp)
        if not_exempted_taxes_not_isp:
            res.append(not_exempted_taxes_not_isp)
        return res

    def build_detalle_no_sujeta(self):
        """ V 1.2
        <element name="DetalleNoSujeta" type="T:DetalleNoSujeta" minOccurs="1"
        maxOccurs="2" />
        <sequence>
            <element name="Causa" type="T:CausaNoSujetaType"/>
            <element name="Importe" type="T:ImporteSgn12.2Type"/>
        </sequence>
        :return: list<OrderedDict>
        """
        not_subject_to_taxes = self.get_not_subject_to_taxes()
        res = []
        if 2 < len(not_subject_to_taxes):
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s: Max. number of not subject to taxes is 2!"
            ) % self.name)
        for tax in not_subject_to_taxes:
            res.append(OrderedDict([
                ("Causa", tax.not_subject_to_cause),
                ("Importe", tax.base)
            ]))
        return res

    def build_detalles_factura(self):
        gipuzkoa_tax_agency = self.env.ref(
            "l10n_es_ticketbai_api.tbai_tax_agency_gipuzkoa")
        araba_tax_agency = self.env.ref(
            "l10n_es_ticketbai_api.tbai_tax_agency_araba")
        tax_agency = self.company_id.tbai_tax_agency_id
        if tax_agency in (gipuzkoa_tax_agency, araba_tax_agency):
            id_detalle_factura = self.build_id_detalle_factura()
            if id_detalle_factura:
                res = {"IDDetalleFactura": id_detalle_factura}
            else:
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Invoice lines are required for the Tax Agency %s!"
                ) % (self.name, tax_agency.name))
        else:
            res = {}
        return res

    def build_emisor(self):
        partner = self.company_id.partner_id
        return OrderedDict([
            ("NIF", partner.tbai_get_value_nif()),
            ("ApellidosNombreRazonSocial",
             partner.tbai_get_value_apellidos_nombre_razon_social())
        ])

    def build_encadenamiento_factura_anterior(self):
        if self.schema == TicketBaiSchema.TicketBai.value and \
                self.previous_tbai_invoice_id:
            signature_value = self.previous_tbai_invoice_id.signature_value
            if not signature_value:
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Previous Invoice signature value is required.") % self.name)
            signature_value = signature_value[:100]
            res = OrderedDict([
                ("SerieFacturaAnterior",
                 self.previous_tbai_invoice_id.number_prefix),
                ("NumFacturaAnterior", self.previous_tbai_invoice_id.number),
                ("FechaExpedicionFacturaAnterior",
                 self.previous_tbai_invoice_id.expedition_date),
                ("SignatureValueFirmaFacturaAnterior", signature_value),
            ])
        else:
            res = {}
        return res

    def build_entrega(self):
        """ V 1.2
        <element name="Entrega" type="T:Entrega" minOccurs="0"/>
            <sequence>
                <element name="Sujeta" type="T:SujetaType" minOccurs="0" />
                <element name="NoSujeta" type="T:NoSujetaType" minOccurs="0" />
            </sequence>
        :return: OrderedDict
        """
        res = OrderedDict()
        sujeta = self.build_sujeta()
        if sujeta:
            res["Sujeta"] = sujeta
        no_sujeta = self.build_no_sujeta()
        if no_sujeta:
            res["NoSujeta"] = no_sujeta
        return res

    def build_exenta(self):
        """ V 1.2
        <element name="DetalleExenta" type="T:DetalleExentaType" minOccurs="1"
                 maxOccurs="7" />
        :return: dict
        """
        exempted_detail = self.build_detalle_exenta()
        if exempted_detail:
            res = {"DetalleExenta": exempted_detail}
        else:
            res = {}
        return res

    def build_factura(self):
        return OrderedDict([
            ("CabeceraFactura", self.build_cabecera_factura()),
            ("DatosFactura", self.build_datos_factura()),
            ("TipoDesglose", self.build_tipo_desglose()),
        ])

    def build_factura_rectificativa(self):
        if self.is_invoice_refund:
            res = OrderedDict([
                ("Codigo", self.refund_code),
                ("Tipo", self.refund_type)
            ])
            importe_rectificacion_sustitutiva = \
                self.build_importe_rectificacion_sustitutiva()
            if importe_rectificacion_sustitutiva:
                res["ImporteRectificacionSustitutiva"] = \
                    importe_rectificacion_sustitutiva
        else:
            res = {}
        return res

    def build_facturas_rectificadas_sustituidas(self):
        res = {}
        if self.is_invoice_refund or \
                SiNoType.S.value == self.substitutes_simplified_invoice:
            refunds_values = []
            for refund in self.tbai_invoice_refund_ids:
                vals = OrderedDict()
                prefix = refund.number_prefix
                if prefix:
                    vals["SerieFactura"] = prefix
                vals["NumFactura"] = refund.number
                vals["FechaExpedicionFactura"] = refund.expedition_date
                refunds_values.append(vals)
            res = {"IDFacturaRectificadaSustituida": refunds_values}
        return res

    def build_huella_tbai(self):
        res = OrderedDict()
        previous_invoice_chaining = self.build_encadenamiento_factura_anterior()
        if previous_invoice_chaining:
            res["EncadenamientoFacturaAnterior"] = previous_invoice_chaining
        res["Software"] = self.company_id.tbai_build_software()
        if self.company_id.tbai_device_serial_number:
            res["NumSerieDispositivo"] = self.company_id.tbai_device_serial_number
        return res

    def build_id_detalle_factura(self):
        if 1000 < len(self.tbai_invoice_line_ids):
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s:\n"
                "Maximum number of Invoice Lines allowed is 1000.") % self.name)
        res = []
        for line in self.tbai_invoice_line_ids:
            res.append(OrderedDict([
                ("DescripcionDetalle", line.description),
                ("Cantidad", line.quantity),
                ("ImporteUnitario", line.price_unit),
                ("Descuento", line.discount_amount or '0.00'),
                ("ImporteTotal", line.amount_total)
            ]))
        return res

    def build_id_factura(self):
        cabecera_factura = OrderedDict()
        if self.number_prefix:
            cabecera_factura["SerieFactura"] = self.number_prefix
        cabecera_factura["NumFactura"] = self.number
        cabecera_factura["FechaExpedicionFactura"] = self.expedition_date
        return OrderedDict([
            ("Emisor", self.build_emisor()),
            ("CabeceraFactura", cabecera_factura)
        ])

    def build_importe_rectificacion_sustitutiva(self):
        if RefundType.substitution.value == self.refund_type:
            res = OrderedDict([
                ("BaseRectificada", self.substituted_invoice_amount_total_untaxed),
                ("CuotaRectificada", self.substituted_invoice_total_tax_amount)
            ])
        else:
            res = {}
        return res

    def build_no_exenta(self):
        """ V 1.2
        <element name="DetalleNoExenta" type="T:DetalleNoExentaType" minOccurs="1"
                 maxOccurs="2" />
        :return: dict
        """
        not_exempted_detail = self.build_detalle_no_exenta()
        if not_exempted_detail:
            res = {"DetalleNoExenta": not_exempted_detail}
        else:
            res = {}
        return res

    def build_no_sujeta(self):
        """ V 1.2
        <element name="NoSujeta" type="T:NoSujetaType" minOccurs="0" />
            <sequence>
                <element name="DetalleNoSujeta" type="T:DetalleNoSujeta" minOccurs="1"
                maxOccurs="2" />
            </sequence>
        :return: OrderedDict
        """
        res = OrderedDict()
        not_subject_to_details = self.build_detalle_no_sujeta()
        if not_subject_to_details:
            res["DetalleNoSujeta"] = not_subject_to_details
        return res

    def build_prestacion_servicios(self):
        """ V 1.2
        <element name="PrestacionServicios" type="T:PrestacionServicios" minOccurs="0"/>
            <sequence>
                <element name="Sujeta" type="T:SujetaType" minOccurs="0" />
                <element name="NoSujeta" type="T:NoSujetaType" minOccurs="0" />
            </sequence>
        :return: OrderedDict
        """
        res = OrderedDict()
        sujeta = self.build_sujeta()
        if sujeta:
            res["Sujeta"] = sujeta
        no_sujeta = self.build_no_sujeta()
        if no_sujeta:
            res["NoSujeta"] = no_sujeta
        return res

    def build_sujeta(self):
        """ V 1.2
        <element name="Sujeta" type="T:SujetaType" minOccurs="0" />
            <sequence>
                <element name="Exenta" type="T:ExentaType" minOccurs="0" />
                <element name="NoExenta" type="T:NoExentaType" minOccurs="0" />
        :return: OrderedDict
        """
        res = OrderedDict()
        exempted = self.build_exenta()
        if exempted:
            res["Exenta"] = exempted
        not_exempted = self.build_no_exenta()
        if not_exempted:
            res["NoExenta"] = not_exempted
        return res

    def build_sujetos(self):
        res = OrderedDict([
            ("Emisor", self.build_emisor())
        ])
        customers = self.build_destinatarios()
        if customers:
            res["Destinatarios"] = customers
        return res

    def build_tipo_desglose(self):
        spain_country_code = self.env.ref('base.es').code.upper()
        spanish_or_no_customers = False
        if 0 == len(self.tbai_customer_ids):
            spanish_or_no_customers = True
        else:
            country_codes = list(set(self.tbai_customer_ids.mapped('country_code')))
            if 1 < len(country_codes):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "All Invoice recipients must be from the same country."
                ) % self.name)
            elif 1 == len(country_codes) and country_codes[0] == spain_country_code:
                # Solo se admite desglose por operación cuando existe destinatario
                # extranjero (tipo IDOtro o que sea un NIF que empiece por N)
                spanish_or_no_customers = not (
                    self.tbai_customer_ids[:1].nif or "").startswith('N')
        if spanish_or_no_customers:
            res = {"DesgloseFactura": OrderedDict()}
            sujeta = self.build_sujeta()
            if sujeta:
                res["DesgloseFactura"]["Sujeta"] = sujeta
            no_sujeta = self.build_no_sujeta()
            if no_sujeta:
                res["DesgloseFactura"]["NoSujeta"] = no_sujeta
        else:
            res = {"DesgloseTipoOperacion": OrderedDict()}
            prestacion_servicios = self.with_context(
                tbai_tax_type=TicketBaiTaxType.service.value
            ).build_prestacion_servicios()
            if prestacion_servicios:
                res["DesgloseTipoOperacion"][
                    "PrestacionServicios"] = prestacion_servicios
            entrega = self.with_context(
                tbai_tax_type=TicketBaiTaxType.provision_of_goods.value).build_entrega()
            if entrega:
                res["DesgloseTipoOperacion"]["Entrega"] = entrega
        return res


class TicketBAIInvoiceRefund(models.Model):
    _name = 'tbai.invoice.refund'
    _description = 'TicketBAI Refunded Invoices'

    tbai_invoice_id = fields.Many2one(
        comodel_name='tbai.invoice', required=True, ondelete='cascade')
    number = fields.Char(required=True)
    number_prefix = fields.Char(default='')
    expedition_date = fields.Char(required=True)

    @api.multi
    @api.constrains('number')
    def _check_number(self):
        for record in self:
            if 20 < len(record.number):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Refunded Invoice Number %s longer than expected. "
                    "Should be 20 characters max.!"
                ) % (record.tbai_invoice_id.name, record.number))

    @api.multi
    @api.constrains('number_prefix')
    def _check_number_prefix(self):
        for record in self:
            if record.number_prefix and 20 < len(record.number_prefix):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Refunded Invoice %s Number Prefix %s longer than expected. "
                    "Should be 20 characters max.!"
                ) % (record.tbai_invoice_id.name, record.number, record.number_prefix))

    @api.multi
    @api.constrains('expedition_date')
    def _check_expedition_date(self):
        for record in self:
            tbai_utils.check_date(_(
                "TicketBAI Invoice %s:\n"
                "Refunded Invoice %s Expedition Date"
            ) % (record.tbai_invoice_id.name, record.number), record.expedition_date)
