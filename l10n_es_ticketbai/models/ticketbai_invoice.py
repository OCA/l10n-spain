# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import qrcode
from urllib.parse import urlencode
import io
import base64
from lxml import etree
from collections import OrderedDict
from enum import Enum
from ..ticketbai.api import TicketBaiApi
from ..ticketbai.xml_schema import XMLSchema, TicketBaiInvoiceTypeEnum, \
    XMLSchemaModeNotSupported
from ..ticketbai.crc8 import crc8
from odoo import models, fields, exceptions, _, api

_logger = logging.getLogger(__name__)


class TicketBaiQRParams(Enum):
    tbai_identifier = 'id'
    invoice_number_prefix = 's'
    invoice_number = 'nf'
    invoice_total_amount = 'i'


class TicketBaiIdentifierValuesIndex(Enum):
    tbai_prefix = 0
    company_vat_number = 1
    invoice_date = 2
    signature_value = 3


class TicketBaiInvoiceState(Enum):
    draft = 'draft'
    pending = 'pending'
    sent = 'sent'
    cancel = 'cancel'


class TicketBAIInvoice(models.AbstractModel):
    _name = 'tbai.invoice'
    _order = "id desc"

    @api.multi
    def _get_ticketbai_api(self):
        self.ensure_one()
        cert = self.company_id.tbai_certificate_id
        error_fields = []
        if not self.api_url:
            error_fields.append("TicketBAI API URL")
        if not cert.public_key or not cert.private_key:
            error_fields.append(_("Certificate credentials"))
        if 0 < len(error_fields):
            raise exceptions.ValidationError(_(
                "TicketBAI missing required fields: %s") % ", ".join(error_fields))
        return TicketBaiApi(self.api_url, cert.public_key, cert.private_key)

    @api.multi
    def send(self, **kwargs):
        self.ensure_one()
        error_msg = ''
        try:
            tbai_api = self._get_ticketbai_api()
        except exceptions.ValidationError as ve:
            _logger.exception(ve)
            tbai_api = None
            error_msg = ve.name
        if tbai_api is not None:
            response = tbai_api.requests_post(base64.decodebytes(self.datas))
            values = self.env['tbai.response'].prepare_tbai_response_values(
                response, **kwargs)
        else:
            values = self.env['tbai.response'].prepare_tbai_error_values(
                error_msg, **kwargs)
        return self.env['tbai.response'].create(values)

    @api.model
    def get_next_pending_invoice(self, company_id=False, limit=1):
        domain = [
            ('state', '=', TicketBaiInvoiceState.pending.value)
        ]
        if company_id:
            domain.append(('company_id', '=', company_id))
        return self.search(domain, order='id ASC', limit=limit)

    @api.model
    def get_pending_invoices(self, company_id=False):
        return self.get_next_pending_invoice(company_id=company_id, limit=0)

    @api.multi
    def cancel(self):
        self.write({'state': TicketBaiInvoiceState.cancel.value})

    @api.multi
    def recreate(self):
        """This method is meant to be override"""
        raise NotImplementedError()

    @api.model
    def cancel_and_recreate_pending_invoices(self, company_id=False):
        pending_invoices = self.get_pending_invoices(company_id=company_id)
        pending_invoices.cancel()
        pending_invoices.recreate()

    name = fields.Char(required=True)
    company_id = fields.Many2one(comodel_name='res.company', required=True)
    signature_value = fields.Char('Signature Value')
    tbai_identifier = fields.Char(
        'TBAI Identifier', compute='_compute_tbai_identifier', store=True)
    qr_url = fields.Char('URL', compute='_compute_tbai_qr', store=True)
    qr = fields.Binary(string="QR", compute='_compute_tbai_qr', store=True)
    datas = fields.Binary()
    datas_fname = fields.Char('File Name')
    file_size = fields.Integer('File Size')
    state = fields.Selection(selection=[
        (TicketBaiInvoiceState.draft.value, 'Draft'),
        (TicketBaiInvoiceState.pending.value, 'Pending'),
        (TicketBaiInvoiceState.sent.value, 'Sent'),
        (TicketBaiInvoiceState.cancel.value, 'Cancelled')
    ], default=TicketBaiInvoiceState.draft.value, required=True, index=True)
    api_url = fields.Char('TicketBAI API URL', compute='_compute_api_url')

    def _get_tbai_identifier_values(self):
        """ V 1.1
        This method is meant to be called by the Models which implement this one (e.g.:
         tbai.invoice.customer.invoice)
        TBAI-<vat_number>-<invoice_date>-<signature_value>
        :return: List of strings
        """
        self.ensure_one()
        return ['TBAI', self.company_id.partner_id.tbai_get_value_nif(), None,
                self.signature_value[:13]]

    def _get_qr_url_values(self):
        """ V 1.1
        This method is meant to be called by the Models which implement this one (e.g.:
         tbai.invoice.customer.invoice)
        <base_url>?id=<tbai_identifier>&s=<invoice_number_prefix>&nf=<invoice_number>
        &i=<invoice_total_amount>&cr=<crc8>
        :return: dict to build query string
        """
        self.ensure_one()
        return OrderedDict([
            (TicketBaiQRParams.tbai_identifier.value, self.tbai_identifier),
            (TicketBaiQRParams.invoice_number_prefix.value, None),
            (TicketBaiQRParams.invoice_number.value, None),
            (TicketBaiQRParams.invoice_total_amount.value, None)
        ])

    def get_tbai_xml_unsigned(self):
        self.ensure_one()
        if self.TicketBAIXMLSchema.mode == TicketBaiInvoiceTypeEnum.customer_invoice:
            my_ordered_dict = self.build_customer_invoice()
        elif self.TicketBAIXMLSchema.mode == \
                TicketBaiInvoiceTypeEnum.customer_cancellation:
            my_ordered_dict = self.build_customer_cancellation()
        else:
            raise XMLSchemaModeNotSupported(
                "TicketBAI - XML Invoice mode not supported!")
        return self.TicketBAIXMLSchema.dict2xml(my_ordered_dict)

    def get_tbai_xml_signed_and_signature_value(self):
        self.ensure_one()
        root = self.get_tbai_xml_unsigned()
        p12 = self.company_id.tbai_certificate_id.get_p12()
        signature_value = XMLSchema.sign(root, p12)
        return root, signature_value

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
                        "TicketBAI Invoice %s Error: TBAI identifier without CRC-8 %s "
                        "should be %d characters long!"
                    ) % (record.invoice_id.number, tbai_identifier_without_crc,
                         tbai_identifier_len_without_crc))
                crc = crc8(tbai_identifier_without_crc)
                values.append(crc)
                tbai_identifier_with_crc = '-'.join(values)
                if tbai_identifier_len_with_crc != len(tbai_identifier_with_crc):
                    raise exceptions.ValidationError(_(
                        "TicketBAI Invoice %s Error: TBAI identifier %s should be "
                        "%d characters long with CRC-8!"
                    ) % (record.invoice_id.number, tbai_identifier_with_crc,
                         tbai_identifier_len_with_crc))
                record.tbai_identifier = tbai_identifier_with_crc

    @api.multi
    @api.depends('tbai_identifier')
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
                qr_values = record._get_qr_url_values()
                qr_url_without_crc = "%s?%s" % (
                    record.company_id.tbai_tax_agency_id.qr_base_url,
                    urlencode(qr_values, encoding='utf-8'))
                qr_crc = crc8(qr_url_without_crc)
                qr_values['cr'] = qr_crc
                qr_url_with_crc = "%s?%s" % (
                    record.company_id.tbai_tax_agency_id.qr_base_url,
                    urlencode(qr_values, encoding='utf-8'))
                record.qr_url = qr_url_with_crc
                # Let QRCode decide the best version when calling make()
                qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M)
                qr.add_data(record.qr_url)
                qr.make()
                img = qr.make_image(fill_color="white", back_color="black")
                with io.BytesIO() as temp:
                    img.save(temp, format="PNG")
                    record.qr = base64.b64encode(temp.getvalue())

    def _compute_api_url(self):
        """This method is meant to be override"""
        raise NotImplementedError()

    def build_tbai_invoice(self):
        self.ensure_one()
        root, signature_value = self.get_tbai_xml_signed_and_signature_value()
        root_str = etree.tostring(root, xml_declaration=True, encoding='utf-8')
        self.datas = base64.b64encode(root_str)
        self.datas_fname = "%s.xsig" % self.name.replace('/', '-')
        self.file_size = len(root_str)
        self.signature_value = signature_value
        self.state = TicketBaiInvoiceState.pending.value

    def build_customer_invoice(self):
        self.ensure_one()
        return {"TicketBai": OrderedDict([
            ("Cabecera", self.tbai_build_cabecera()),
            ("Sujetos", self.tbai_build_sujetos()),
            ("Factura", self.tbai_build_factura()),
            ("HuellaTBAI", self.tbai_build_huella_tbai()),
        ])}

    def build_customer_cancellation(self):
        self.ensure_one()
        return {"AnulaTicketBai": OrderedDict([
            ("Cabecera", self.tbai_build_cabecera()),
            ("IDFactura", self.tbai_build_id_factura()),
            ("HuellaTBAI", self.tbai_build_huella_tbai()),
        ])}

    def tbai_build_cabecera(self):
        """ V 1.1
        Get TicketBAI version from the Company Tax Agency.

        <element name="Cabecera" type="T:Cabecera"/>
        <complexType name="Cabecera">
            <sequence>
                <element name="IDVersionTBAI" type="T:TextMax5Type"/>
            </sequence>
        </complexType>
        :return: Tax Agency
        """
        tax_agency = self.company_id.tbai_tax_agency_id
        return {"IDVersionTBAI": tax_agency.tbai_get_value_id_version_tbai()}
