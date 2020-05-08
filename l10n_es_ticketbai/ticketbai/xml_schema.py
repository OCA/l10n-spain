# -*- coding: utf-8 -*-
# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import xmlsig
from datetime import datetime
from base64 import b64encode
from uuid import uuid4
from cryptography.hazmat.primitives import hashes
from lxml import etree
import logging
import re
import os
from enum import Enum

_logger = logging.getLogger(__name__)


class XMLSchemaException(Exception):
    def __init__(self, name, value=None):
        if type(self) == XMLSchemaException:
            _logger.warning("You should implement a non generic Exception for your particular use case.")
        self.name = name
        self.value = value
        self.args = (name, value)


class XMLSchemaConstraints(XMLSchemaException):
    """Violation of schema constraints"""
    def __init__(self, msg):
        super(XMLSchemaConstraints, self).__init__(msg)


class XMLSchemaModeNotSupported(XMLSchemaException):
    """Mode - Invoice file type not supported"""
    def __init__(self, msg):
        super(XMLSchemaModeNotSupported, self).__init__(msg)


class TicketBaiInvoiceTypeEnum(Enum):
    customer_invoice = 'customer_invoice'
    customer_cancellation = 'customer_cancellation'


class XMLSchema:

    version = 'V 1.1'
    schemas_version_dirname = "v1.1"
    ns = 'http://www.w3.org/2001/XMLSchema'
    default_min_occurs = 1
    tags_to_ignore = [
        "{%s}complexType" % ns,
        "{%s}sequence" % ns
    ]
    choice_tag = "{%s}choice" % ns

    def __init__(self, mode):
        script_dirpath = os.path.abspath(os.path.dirname(__file__))
        if mode == TicketBaiInvoiceTypeEnum.customer_invoice:
            xml_filepath = os.path.join(script_dirpath, 'schemas/%s/ticketBai V1-1.xsd' % self.schemas_version_dirname)
            self.invoice_ns = 'http://ticketbai.eus'
        elif mode == TicketBaiInvoiceTypeEnum.customer_cancellation:
            xml_filepath = os.path.join(
                script_dirpath, 'schemas/%s/Anula_ticketBai V1-1.xsd' % self.schemas_version_dirname)
            self.invoice_ns = 'http://ticketbai.eus/anulacion'
        else:
            raise XMLSchemaModeNotSupported("TicketBai - XML Invoice mode not supported!")
        self.invoice_nsmap = {
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'etsi': 'http://uri.etsi.org/01903/v1.3.2#',
            'T': self.invoice_ns
        }
        self.xml_filename = xml_filepath
        # Use parser ETCompatXMLParser to avoid the following error while running some particular test cases:
        # File "b'/path/to/l10n_es_ticketbai/ticketbai/schemas/v1.1/test_ticketBai V1-1.xsd'", line 0
        # lxml.etree.XMLSyntaxError: <no detail available>
        # The error was found using Python 3.7.3 and lxml-4.3.2 (default for Debian 10 Buster)
        self.xmlschema_doc = etree.parse(xml_filepath, parser=etree.ETCompatXMLParser())

    @staticmethod
    def xml_is_valid(test_xmlschema_doc, root):
        """
        :param test_xmlschema_doc: Parsed XSD file with Xades imports
        :param root: xml
        :return: bool
        """
        schema = etree.XMLSchema(test_xmlschema_doc)
        try:
            schema.assertValid(root)
            valid = True
        except etree.DocumentInvalid as error:
            _logger.exception(error)
            valid = False
        return valid

    @staticmethod
    def sign(root, certificate):
        """
        Sign XML with PKCS #12
        :author: Victor Laskurain <blaskurain@binovo.es>
        :return: SignatureValue
        """

        def create_node_tree(root, elem_list):
            """Convierte una lista en XML.

            Cada elemento de la lista se interpretará de la siguiente manera:

            Si es un string se añadirá al texto suelto del nodo root.
            Si es una tupla/lista t se interpretará como sigue:
                t[0]  es el nombre del elemento a crear. Puede tener prefijo de espacio de nombres.
                t[1]  es la lista de atributos donde las posiciones pares son claves y los impares valores.
                t[2:] son los subelementos que se interpretan recursivamente
            """
            for elem_def in elem_list:
                if isinstance(elem_def, str):
                    root.text = (root.text or '') + elem_def
                else:
                    ns = ''
                    elemname = elem_def[0]
                    attrs = elem_def[1]
                    children = elem_def[2:]
                    if ':' in elemname:
                        ns, elemname = elemname.split(':')
                        ns = root.nsmap[ns]
                    node = xmlsig.utils.create_node(elemname, root, ns)
                    for attr_name, attr_value in zip(attrs[::2], attrs[1::2]):
                        node.set(attr_name, attr_value)
                    create_node_tree(node, children)

        doc_id = 'id-' + str(uuid4())
        signature_id = 'sig-' + doc_id
        kinfo_id = 'ki-' + doc_id
        sp_id = 'sp-' + doc_id
        signature = xmlsig.template.create(
            xmlsig.constants.TransformInclC14N,
            xmlsig.constants.TransformRsaSha256,
            signature_id,
        )
        ref = xmlsig.template.add_reference(
            signature, xmlsig.constants.TransformSha256
        )
        xmlsig.template.add_transform(ref, xmlsig.constants.TransformEnveloped)
        xmlsig.template.add_reference(
            signature, xmlsig.constants.TransformSha256, uri='#' + kinfo_id
        )
        xmlsig.template.add_reference(
            signature, xmlsig.constants.TransformSha256, uri="#" + sp_id
        )
        ki = xmlsig.template.ensure_key_info(signature, name=kinfo_id)
        data = xmlsig.template.add_x509_data(ki)
        xmlsig.template.x509_data_add_certificate(data)
        xmlsig.template.add_key_value(ki)
        ctx = xmlsig.SignatureContext()
        ctx.load_pkcs12(certificate)
        ctx.x509 = certificate.get_certificate().to_cryptography()
        ctx.public_key = ctx.x509.public_key()
        ctx.private_key = certificate.get_privatekey().to_cryptography_key()
        dslist = ('ds:Object', (),
                  ('etsi:QualifyingProperties', ('Target', signature_id),
                   ('etsi:SignedProperties', ('Id', sp_id),
                    ('etsi:SignedSignatureProperties', (),
                     ('etsi:SigningTime', (), datetime.now().isoformat()),
                     ('etsi:SigningCertificateV2', (),
                      ('etsi:Cert', (),
                       ('etsi:CertDigest', (),
                        ('ds:DigestMethod', ('Algorithm', 'http://www.w3.org/2000/09/xmldsig#sha256')),
                        ('ds:DigestValue', (), b64encode(ctx.x509.fingerprint(hashes.SHA256())).decode())))),
                     ('etsi:SignaturePolicyIdentifier', (),
                      ('etsi:SignaturePolicyId', (),
                       ('etsi:SigPolicyId', (),
                        ('etsi:Identifier', (), 'https://www.gipuzkoa.eus/documents/2456431/12093238/TicketBAI_Pol%C3%ADtica_firma_v_1_0.pdf/3c6e5431-bb1d-34ed-5b26-206aaf085452'),
                        ('etsi:Description', (), 'Política de Firma TicketBAI 1.0')),
                       ('etsi:SigPolicyHash', (),
                        ('ds:DigestMethod', ('Algorithm', 'http://www.w3.org/2000/09/xmldsig#sha256')),
                        ('ds:DigestValue', (), 'lX1xDvBVAsPXkkJ7R07WCVbAm9e0H33I1sCpDtQNkbc='))))))))
        root.append(signature)
        create_node_tree(signature, [dslist])
        ctx.sign(signature)
        signature_value = signature.find('ds:SignatureValue', namespaces=xmlsig.constants.NS_MAP).text
        # RFC2045 - Base64 Content-Transfer-Encoding (page 25)
        # Any characters outside of the base64 alphabet are to be ignored in base64-encoded data.
        return signature_value.replace('\n', '')

    def create_node_from_dict(self, xml_root, key, value):
        if isinstance(value, dict):
            xml_element = etree.SubElement(xml_root, key)
            for subkey, subvalue in value.items():
                self.create_node_from_dict(xml_element, subkey, subvalue)
        elif isinstance(value, list):
            for list_element in value:
                xml_element = etree.SubElement(xml_root, key)
                # NOTE: All list elements are expected to be of type dict
                for subkey, subvalue in list_element.items():
                    self.create_node_from_dict(xml_element, subkey, subvalue)
        else:
            xml_element = etree.SubElement(xml_root, key)
            xml_element.text = value

    def dict2xml(self, invoice_ordered_dict):
        tag = next(iter(invoice_ordered_dict))
        root = etree.Element("{%s}%s" % (self.invoice_ns, tag), nsmap=self.invoice_nsmap)
        ticketbai_dict = invoice_ordered_dict.get(tag)
        for key, value in ticketbai_dict.items():
            self.create_node_from_dict(root, key, value)
        return root

    def xpath(self, node, path):
        return node.xpath(path, namespaces={'ns': self.ns})

    def get_root(self):
        root = self.xmlschema_doc.getroot()
        res = self.xpath(root, "./ns:element")
        if res and 1 < len(res):
            raise XMLSchemaConstraints("Found multiple root element groups...")
        elif res and 1 == len(res):
            root_element = res[0]
        else:
            root_element = None
        return root_element

    def get_element_name(self, element):
        return element.attrib.get('name', None)

    def get_element_type(self, element):
        _, type_name = 'type' in element.attrib and element.attrib.get('type').split(':') or (None, None)
        return type_name

    def is_element_required(self, element):
        return 0 < self.get_element_min_occurs(element) or False

    def get_element_min_occurs(self, element):
        return int(element.attrib.get('minOccurs', self.default_min_occurs))

    def get_element_max_occurs(self, element):
        res = element.attrib.get('maxOccurs', None)
        return int(res) if res is not None else res

    def get_element_ref(self, element):
        return element.attrib.get('ref', None)

    def get_element_value(self, element):
        return element.attrib.get('value')

    def get_node_children(self, node):
        children = node.getchildren()
        if 1 == len(children) and children[0].tag in self.tags_to_ignore:
            children = self.get_node_children(children[0])
        return children

    def node_is_choice(self, node):
        return node.tag == self.choice_tag

    def get_complex_node(self, element):
        type_name = self.get_element_type(element)
        res = self.xpath(self.xmlschema_doc, "//ns:complexType[@name='%s']" % type_name)
        if res and 1 < len(res):
            element_name = self.get_element_name(element)
            raise XMLSchemaConstraints("Found multiple complex nodes for element %s" % element_name)
        elif res and 1 == len(res):
            complex_node = res[0]
        else:
            complex_node = None
        return complex_node

    def element_is_complex_type(self, element):
        res = self.get_complex_node(element)
        return res is not None

    def get_element_simple_type_node(self, element):
        type_name = self.get_element_type(element)
        res = self.xpath(self.xmlschema_doc, "//ns:simpleType[@name='%s']" % type_name)
        if res and 1 < len(res):
            element_name = self.get_element_name(element)
            raise XMLSchemaConstraints("Found multiple simple nodes for element %s" % element_name)
        elif res and 1 == len(res):
            simple_node = res[0]
        else:
            simple_node = None
        return simple_node

    def element_is_simple_type(self, element):
        res = self.get_element_simple_type_node(element)
        return res is not None

    def get_simple_type_attrib_length(self, node):
        res = self.xpath(node, ".//ns:restriction//ns:length")
        if res and 1 < len(res):
            element_name = self.get_element_name(node)
            raise XMLSchemaConstraints("Found multiple length nodes for element %s" % element_name)
        elif res and 1 == len(res):
            length_element = res[0]
        else:
            length_element = None
        return length_element

    def get_simple_type_attrib_length_value(self, node):
        length_element = self.get_simple_type_attrib_length(node)
        if length_element is not None:
            res = int(self.get_element_value(length_element))
        else:
            res = None
        return res

    def get_simple_type_attrib_max_length(self, node):
        res = self.xpath(node, ".//ns:restriction//ns:maxLength")
        if res and 1 < len(res):
            element_name = self.get_element_name(node)
            raise XMLSchemaConstraints("Found multiple maxLength nodes for element %s" % element_name)
        elif res and 1 == len(res):
            max_length_element = res[0]
        else:
            max_length_element = None
        return max_length_element

    def get_simple_type_attrib_max_length_value(self, node):
        max_length_element = self.get_simple_type_attrib_max_length(node)
        if max_length_element is not None:
            res = int(self.get_element_value(max_length_element))
        else:
            res = None
        return res

    def get_simple_type_attrib_pattern(self, node):
        res = self.xpath(node, ".//ns:restriction//ns:pattern")
        if res and 1 < len(res):
            element_name = self.get_element_name(node)
            raise XMLSchemaConstraints("Found multiple pattern nodes for element %s" % element_name)
        elif res and 1 == len(res):
            pattern_element = res[0]
        else:
            pattern_element = None
        return pattern_element

    def get_simple_type_attrib_pattern_value(self, node):
        pattern_element = self.get_simple_type_attrib_pattern(node)
        if pattern_element is not None:
            res = self.get_element_value(pattern_element)
        else:
            res = None
        return res

    def get_simple_type_attrib_enumerations(self, node):
        return self.xpath(node, ".//ns:restriction//ns:enumeration")

    def get_simple_type_attrib_enumerations_value(self, node):
        enumeration_elements = self.get_simple_type_attrib_enumerations(node)
        return [self.get_element_value(x) for x in enumeration_elements]

    def element_check_value(self, invoice_reference, element, value):
        element_name = self.get_element_name(element)
        node = self.get_element_simple_type_node(element)
        length = self.get_simple_type_attrib_length_value(node)
        max_length = self.get_simple_type_attrib_max_length_value(node)
        enumerations = self.get_simple_type_attrib_enumerations_value(node)
        pattern = self.get_simple_type_attrib_pattern_value(node)

        if length is not None and length != len(value):
            raise XMLSchemaConstraints(
                "TicketBAI Invoice %s Error: Element %s value %s should be %d characters long!" % (
                    invoice_reference, element_name, value, length))
        elif max_length is not None and max_length < len(value):
            raise XMLSchemaConstraints(
                "TicketBAI Invoice %s Error: Element %s value %s should be max %d characters long!" % (
                    invoice_reference, element_name, value, max_length))
        elif 0 < len(enumerations):
            value_found = False
            i = 0
            while not value_found and i < len(enumerations):
                enum_value = enumerations[i]
                if enum_value == value:
                    value_found = True
                i += 1
            if not value_found:
                raise XMLSchemaConstraints(
                    "TicketBAI Invoice %s Error: Element %s value %s not supported!" % (
                        invoice_reference, value, element_name))
        if pattern:
            match_res = re.match(pattern, value)
            if not match_res or (match_res and match_res.group(0) != value):
                raise XMLSchemaConstraints(
                    "TicketBAI Invoice %s Error: Element %s value %s format not valid!" % (
                        invoice_reference, value, element_name))
