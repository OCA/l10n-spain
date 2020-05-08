# -*- coding: utf-8 -*-
# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import qrcode
from urllib.parse import urlencode
import io
import base64
from lxml import etree
from collections import OrderedDict
from enum import Enum
from ..ticketbai.xml_schema import XMLSchema, XMLSchemaConstraints
from ..ticketbai.crc8 import crc8
from odoo import models, fields, exceptions, _, api


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


class TicketBAIInvoice(models.AbstractModel):
    _name = 'tbai.invoice'
    _order = "id desc"

    name = fields.Char(required=True)
    company_id = fields.Many2one(comodel_name='res.company', required=True)
    signature_value = fields.Char('Signature Value')
    tbai_identifier = fields.Char('TBAI Identifier', compute='_compute_tbai_identifier', store=True)
    qr_url = fields.Char('URL', compute='_compute_tbai_qr', store=True)
    qr = fields.Binary(string="QR", compute='_compute_tbai_qr', store=True)
    datas = fields.Binary()
    datas_fname = fields.Char('File Name')
    file_size = fields.Integer('File Size')

    def _get_tbai_identifier_values(self):
        """ V 1.1
        This method is meant to be called by the Models which implement this one (e.g.: tbai.invoice.customer.invoice)
        TBAI-<vat_number>-<invoice_date>-<signature_value>
        :return: List of strings
        """
        self.ensure_one()
        return ['TBAI', self.company_id.partner_id.tbai_get_value_NIF(), None, self.signature_value[:13]]

    def _get_qr_url_values(self):
        """ V 1.1
        This method is meant to be called by the Models which implement this one (e.g.: tbai.invoice.customer.invoice)
        <base_url>?id=<tbai_identifier>&s=<invoice_number_prefix>&nf=<invoice_number>&i=<invoice_total_amount>&cr=<crc8>
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
        my_ordered_dict = self.build_invoice()
        return self.TicketBAIXMLSchema.dict2xml(my_ordered_dict)

    def get_tbai_xml_signed_and_signature_value(self):
        self.ensure_one()
        root = self.get_tbai_xml_unsigned()
        p12 = self.company_id.tbai_aeat_certificate_id.get_p12()
        signature_value = XMLSchema.sign(root, p12)
        return root, signature_value

    @api.one
    @api.depends('signature_value')
    def _compute_tbai_identifier(self):
        if self.signature_value:
            tbai_identifier_length_without_crc = 36
            tbai_identifier_length_with_crc = 39
            values = self._get_tbai_identifier_values()
            tbai_identifier_without_crc = '-'.join(values) + '-'
            if tbai_identifier_length_without_crc != len(tbai_identifier_without_crc):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s Error: TBAI identifier without CRC-8 %s should be %d characters long!"
                ) % (self.invoice_id.number, tbai_identifier_without_crc, tbai_identifier_length_without_crc))
            crc = crc8(tbai_identifier_without_crc)
            values.append(crc)
            tbai_identifier_with_crc = '-'.join(values)
            if tbai_identifier_length_with_crc != len(tbai_identifier_with_crc):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s Error: TBAI identifier with CRC-8 %s should be %d characters long!"
                ) % (self.invoice_id.number, tbai_identifier_with_crc, tbai_identifier_length_with_crc))
            self.tbai_identifier = tbai_identifier_with_crc

    @api.one
    @api.depends('tbai_identifier')
    def _compute_tbai_qr(self):
        """ V 1.1
        Código QR TBAI, que consiste en un código con formato QR de tamaño mayor o igual a 30x30 milímetros y
        menor o igual a 40x40 milímetros (en adelante, QR TBAI).
        El nivel de corrección de errores del QR será M.
        La codificación utilizada para la generación del código será UTF-8.
        """
        if self.tbai_identifier:
            qr_values = self._get_qr_url_values()
            qr_url_without_crc = "%s?%s" % (
                self.company_id.tbai_tax_agency_id.qr_base_url, urlencode(qr_values, encoding='utf-8'))
            qr_crc = crc8(qr_url_without_crc)
            qr_values['cr'] = qr_crc
            qr_url_with_crc = "%s?%s" % (
                self.company_id.tbai_tax_agency_id.qr_base_url, urlencode(qr_values, encoding='utf-8'))
            self.qr_url = qr_url_with_crc
            # Let QRCode decide the best version when calling make()
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M)
            qr.add_data(self.qr_url)
            qr.make()
            img = qr.make_image(fill_color="white", back_color="black")
            with io.BytesIO() as temp:
                img.save(temp, format="PNG")
                self.qr = base64.b64encode(temp.getvalue())

    def _build_tbai_invoice(self):
        self.ensure_one()
        root, signature_value = self.get_tbai_xml_signed_and_signature_value()
        root_str = etree.tostring(root, xml_declaration=True, encoding='utf-8')
        self.datas = base64.b64encode(root_str)
        self.datas_fname = "%s.xsig" % self.name.replace('/', '-')
        self.file_size = len(root_str)
        self.signature_value = signature_value

    def is_element_required(self, element):
        element_name = self.TicketBAIXMLSchema.get_element_name(element)
        tbai_agency_invoice = self.env['tbai.tax.agency.invoice'].search([
            ('tbai_tax_agency_id', '=', self.company_id.tbai_tax_agency_id.id),
            ('name', '=', element_name)
        ])
        if 1 == len(tbai_agency_invoice):
            element_required = 0 < tbai_agency_invoice.min_occurs
        else:
            element_required = self.TicketBAIXMLSchema.is_element_required(element)
        return element_required

    def get_element_max_occurs(self, element):
        element_name = self.TicketBAIXMLSchema.get_element_name(element)
        tbai_agency_invoice = self.env['tbai.tax.agency.invoice'].search([
            ('tbai_tax_agency_id', '=', self.company_id.tbai_tax_agency_id.id),
            ('name', '=', element_name)
        ])
        if 1 == len(tbai_agency_invoice):
            max_occurs = tbai_agency_invoice.max_occurs
        else:
            max_occurs = self.TicketBAIXMLSchema.get_element_max_occurs(element)
        return max_occurs

    def get_element_min_occurs(self, element):
        element_name = self.TicketBAIXMLSchema.get_element_name(element)
        tbai_agency_invoice = self.env['tbai.tax.agency.invoice'].search([
            ('tbai_tax_agency_id', '=', self.company_id.tbai_tax_agency_id.id),
            ('name', '=', element_name)
        ])
        if 1 == len(tbai_agency_invoice):
            min_occurs = tbai_agency_invoice.min_occurs
        else:
            min_occurs = self.TicketBAIXMLSchema.get_element_min_occurs(element)
        return min_occurs

    def get_element_context_records(self, records, element):
        """
        Call record function 'tbai_get_context_records_<element_name>'.
        e.g.: 'tbai_get_context_records_Cabecera' from 'tbai.invoice.customer.invoice' record.
        :param records: Odoo Record/Recordset
        :param element: XML <element ...> node
        :return: Odoo Record/Recordset (e.g.: TicketBAI Tax Agency) or None
        """
        element_name = self.TicketBAIXMLSchema.get_element_name(element)
        res = None
        func = getattr(records, "tbai_get_context_records_%s" % element_name, None)
        if func is not None:
            res = func()
        return res

    def get_element_value(self, records, element):
        """
        Call record function 'tbai_get_value_<element_name>'.
        e.g.: 'tbai_get_value_IDVersionTBAI' from 'tbai.tax.agency' record.
        :param records: Odoo Record/Recordset
        :param element: XML <element ...> node
        :return: dict (e.g.: {'IDVersionTBAI': 'V 1.0'})
        """
        element_name = self.TicketBAIXMLSchema.get_element_name(element)
        simple_type_node = self.TicketBAIXMLSchema.get_element_simple_type_node(element)
        length = self.TicketBAIXMLSchema.get_simple_type_attrib_length_value(simple_type_node)
        max_length = self.TicketBAIXMLSchema.get_simple_type_attrib_max_length_value(simple_type_node)
        pattern = self.TicketBAIXMLSchema.get_simple_type_attrib_pattern_value(simple_type_node)
        enumerations = self.TicketBAIXMLSchema.get_simple_type_attrib_enumerations_value(simple_type_node)
        res = {}
        func = getattr(records, "tbai_get_value_%s" % element_name, None)
        if func is not None:
            value = func(length=length, max_length=max_length, pattern=pattern, enumerations=enumerations)
            if value:
                self.TicketBAIXMLSchema.element_check_value(self.name, element, value)
                res.setdefault(element_name, value)
        return res

    def build_complex_type(self, parent_context_records, element, check_required=True):
        """
        <complexType name="...">
            <sequence>
                [<choice>[<element ...>, ...]</choice>]
                <element ...>
            </sequence>
        </complexType>
        :param parent_context_records: Odoo Record/Recordset
        :param element: XML <element ...> node
        :param check_required: Added for choice elements
        :return: dict
        """
        res = OrderedDict({})
        element_name = self.TicketBAIXMLSchema.get_element_name(element)
        element_required = check_required and self.is_element_required(element) or False
        max_occurs = self.get_element_max_occurs(element)
        min_occurs = self.get_element_min_occurs(element)
        if max_occurs is None or 0 < max_occurs:
            # Build each element passing parent context Record/Recordset
            # Get context Record/Recordset
            context_records = self.get_element_context_records(parent_context_records, element)
            if element_required:
                if (isinstance(context_records, list) or isinstance(context_records, tuple)) and \
                        0 < len(context_records):
                    # e.g.: context_records -> [my.model(), ...] or (my.model(), ...)
                    context_records = [x for x in context_records if x]
                if not context_records:
                    raise exceptions.ValidationError(_(
                        "TicketBAI Invoice %s Error: required complexType %s not implemented!"
                    ) % (self.name, element_name))
                elif min_occurs > len(context_records):
                    raise exceptions.ValidationError(_(
                        "TicketBAI Invoice %s Error: required complexType %s requires a minimum of %d values!"
                    ) % (self.name, element_name, min_occurs))
            elif context_records is None:
                context_records = []
            context_record_res_list = []
            for context_record in context_records:
                if not context_record:
                    continue
                context_record_res = OrderedDict({})
                # Call build_element for each complex node element
                # Get complexType node: <complexType ...>
                complex_node = self.TicketBAIXMLSchema.get_complex_node(element)
                # Get complexType node elements: [<element ...>]
                complex_node_children = self.TicketBAIXMLSchema.get_node_children(complex_node)
                for child in complex_node_children:
                    if self.TicketBAIXMLSchema.node_is_choice(child):
                        # Build exclusive groups <choice>[<element ...>, ...]</choice>
                        # V 1.1: at least one choice is required on all three cases
                        #  - IDDestinatario
                        #  - TipoDesgloseType
                        #  - EntidadDesarrolladoraType
                        choices = self.TicketBAIXMLSchema.get_node_children(child)
                        group_res = OrderedDict({})
                        i = 0
                        while not group_res and i < len(choices):
                            choice = choices[i]
                            group_res.update(self.build_element(context_record, choice, check_required=False))
                            i += 1
                        if not group_res:
                            group_elements_str = ", ".join(
                                [self.TicketBAIXMLSchema.get_element_name(x) for x in choices])
                            raise exceptions.ValidationError(_(
                                "TicketBAI Invoice %s Error: Element %s. "
                                "Empty value for exclusive group with the following elements:\n%s"
                            ) % (self.name, element_name, group_elements_str))
                        else:
                            context_record_res.update(group_res)
                    else:
                        context_record_res.update(
                            self.build_element(context_record, child))
                if context_record_res:
                    context_record_res_list.append(context_record_res)
            if (max_occurs is None or 1 < max_occurs) and 0 < len(context_record_res_list):
                if (max_occurs is not None and len(context_record_res_list) > max_occurs) or \
                        (max_occurs is None and 1 < len(context_record_res_list)):
                    raise exceptions.ValidationError(_(
                        "TicketBAI Invoice %s Error: Element %s. "
                        "Too many results. Max allowed %d") % (self.name, element_name, max_occurs))
                if max_occurs is None:
                    res = OrderedDict({element_name: context_record_res_list[0]})
                else:
                    res = OrderedDict({element_name: context_record_res_list})
            elif 1 == len(context_record_res_list):
                res = OrderedDict({element_name: context_record_res_list[0]})
        return res

    def build_simple_type(self, context_records, element, check_required=True):
        """
        <simpleType name="...">
            [
                <pattern ...>,
                <maxLenght ...>,
                <length ...>,
                [<enumeration value="...">, ...]
            ]
        </simpleType>
        :param context_records: Odoo Record/Recordset
        :param element: XML <element ...> node
        :param check_required: Added for choice elements
        :return: dict
        """
        element_required = check_required and self.is_element_required(element) or False
        # Get build func
        res = self.get_element_value(context_records, element)
        if not res and element_required:
            element_name = self.TicketBAIXMLSchema.get_element_name(element)
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s Error: required simpleType %s not implemented!") % (self.name, element_name))
        return res

    def build_element(self, context_records, element, check_required=True):
        """
        Build element dict value
        :param context_records: Odoo Record/Recordset
        :param element: XML <element ...> node
        :param check_required: Added for choice elements
        :return: dict
        """
        res = OrderedDict({})
        try:
            if self.TicketBAIXMLSchema.element_is_complex_type(element):
                res = self.build_complex_type(context_records, element, check_required=check_required)
            elif self.TicketBAIXMLSchema.element_is_simple_type(element):
                res = self.build_simple_type(context_records, element, check_required=check_required)
        except XMLSchemaConstraints as xml_schema_constraints_exception:
            raise xml_schema_constraints_exception
        except exceptions.ValidationError as ve:
            raise ve
        return res

    def build_invoice(self):
        self.ensure_one()
        lxml_root_element = self.TicketBAIXMLSchema.get_root()
        root_element_name = self.TicketBAIXMLSchema.get_element_name(lxml_root_element)
        res = OrderedDict({root_element_name: OrderedDict({})})
        for element in self.TicketBAIXMLSchema.get_node_children(lxml_root_element):
            res[root_element_name].update(self.build_element(self, element))
        return res

    def tbai_get_context_records_Cabecera(self):
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
        return self.company_id.tbai_tax_agency_id

    def tbai_get_context_records_Sujetos(self):
        """ V 1.1
        Get Company and Customer from the Invoice.
        NOTE: multiple customers not supported

        <element name="Sujetos" type="T:Sujetos"/>
        <complexType name="Sujetos">
            <sequence>
                <element name="Emisor" type="T:Emisor"/>
                <element name="Destinatarios" type="T:Destinatarios" minOccurs="0"/>
                <element name="VariosDestinatarios" type="T:SiNoType" default="N" minOccurs="0"/>
                <element name="EmitidaPorTercerosODestinatario" type="T:EmitidaPorTercerosType" minOccurs="0"/>
            </sequence>
        </complexType>
        :return: Invoice
        """
        # This method is intended to be override
        pass

    def tbai_get_context_records_Factura(self):
        """ V 1.1
        Get Invoice header, Invoice data and Taxes breakdown

        <element name="Factura" type="T:Factura"/>
        <complexType name="Factura">
            <sequence>
                <element name="CabeceraFactura" type="T:CabeceraFacturaType"/>
                <element name="DatosFactura" type="T:DatosFacturaType"/>
                <element name="TipoDesglose" type="T:TipoDesgloseType"/>
            </sequence>
        </complexType>
        :return: Invoice
        """
        # This method is intended to be override
        pass
