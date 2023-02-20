# Copyright 2020 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from base64 import b64encode
from datetime import datetime
from uuid import uuid4

import xmlsig
import xmltodict
from cryptography.hazmat.primitives import hashes
from lxml import etree

from ..utils import utils as tbai_utils

_logger = logging.getLogger(__name__)


class XMLSchemaException(Exception):
    def __init__(self, name, value=None):
        if type(self) == XMLSchemaException:
            _logger.warning(
                "You should implement a non generic Exception for your particular use "
                "case."
            )
        self.name = name
        self.value = value
        self.args = (name, value)


class XMLSchemaModeNotSupported(XMLSchemaException):
    def __init__(self, msg):
        super(XMLSchemaModeNotSupported, self).__init__(msg)


class TicketBaiSchema(tbai_utils.EnumValues):
    TicketBai = "TicketBai"
    AnulaTicketBai = "AnulaTicketBai"
    TicketBaiResponse = "TicketBaiResponse"


class XMLSchema:
    version = "1.2"
    schemas_version_dirname = "v1.2"
    ns = "http://www.w3.org/2001/XMLSchema"
    default_min_occurs = 1
    tags_to_ignore = ["{%s}complexType" % ns, "{%s}sequence" % ns]
    choice_tag = "{%s}choice" % ns

    def __init__(self, mode):
        if mode == TicketBaiSchema.TicketBai.value:
            invoice_ns = "urn:ticketbai:emision"
        elif mode == TicketBaiSchema.AnulaTicketBai.value:
            invoice_ns = "urn:ticketbai:anulacion"
        elif mode == TicketBaiSchema.TicketBaiResponse.value:
            invoice_ns = "urn:ticketbai:emision"
        else:
            raise XMLSchemaModeNotSupported(
                "TicketBAI - XML Invoice mode not supported!"
            )
        self.mode = mode
        self.invoice_ns = invoice_ns
        self.invoice_nsmap = {
            "ds": "http://www.w3.org/2000/09/xmldsig#",
            "etsi": "http://uri.etsi.org/01903/v1.3.2#",
            "T": self.invoice_ns,
        }

    @staticmethod
    def xml_is_valid(test_xmlschema_doc, root):
        """
        :param test_xmlschema_doc: Parsed XSD file with Xades imports
        :param root: xml
        :return: bool
        """
        schema = etree.XMLSchema(test_xmlschema_doc)
        return schema(root)

    @staticmethod
    def sign(root, certificate, tax_agency):
        """
        Sign XML with PKCS #12
        :author: Victor Laskurain <blaskurain@binovo.es>
        :return: SignatureValue
        """

        def create_node_tree(root_node, elem_list):
            """Convierte una lista en XML.

            Cada elemento de la lista se interpretará de la siguiente manera:

            Si es un string se añadirá al texto suelto del nodo root.
            Si es una tupla/lista t se interpretará como sigue:
                t[0]  es el nombre del elemento a crear. Puede tener prefijo de espacio
                de nombres.
                t[1]  es la lista de atributos donde las posiciones pares son claves y
                los impares valores.
                t[2:] son los subelementos que se interpretan recursivamente
            """
            for elem_def in elem_list:
                if isinstance(elem_def, str):
                    root_node.text = (root_node.text or "") + elem_def
                else:
                    ns = ""
                    elemname = elem_def[0]
                    attrs = elem_def[1]
                    children = elem_def[2:]
                    if ":" in elemname:
                        ns, elemname = elemname.split(":")
                        ns = root_node.nsmap[ns]
                    node = xmlsig.utils.create_node(elemname, root_node, ns)
                    for attr_name, attr_value in zip(attrs[::2], attrs[1::2]):
                        node.set(attr_name, attr_value)
                    create_node_tree(node, children)

        doc_id = "id-" + str(uuid4())
        signature_id = "sig-" + doc_id
        kinfo_id = "ki-" + doc_id
        sp_id = "sp-" + doc_id
        signature = xmlsig.template.create(
            xmlsig.constants.TransformInclC14N,
            xmlsig.constants.TransformRsaSha256,
            signature_id,
        )
        ref = xmlsig.template.add_reference(
            signature, xmlsig.constants.TransformSha256, uri=""
        )
        xmlsig.template.add_transform(ref, xmlsig.constants.TransformEnveloped)
        xmlsig.template.add_reference(
            signature, xmlsig.constants.TransformSha256, uri="#" + kinfo_id
        )
        xmlsig.template.add_reference(
            signature,
            xmlsig.constants.TransformSha256,
            uri="#" + sp_id,
            uri_type="http://uri.etsi.org/01903#SignedProperties",
        )
        ki = xmlsig.template.ensure_key_info(signature, name=kinfo_id)
        data = xmlsig.template.add_x509_data(ki)
        xmlsig.template.x509_data_add_certificate(data)
        xmlsig.template.add_key_value(ki)
        ctx = xmlsig.SignatureContext()
        ctx.x509 = certificate[1]
        ctx.public_key = ctx.x509.public_key()
        ctx.private_key = certificate[0]
        dslist = (
            "ds:Object",
            (),
            (
                "etsi:QualifyingProperties",
                ("Target", "#" + signature_id),
                (
                    "etsi:SignedProperties",
                    ("Id", sp_id),
                    (
                        "etsi:SignedSignatureProperties",
                        (),
                        ("etsi:SigningTime", (), datetime.now().isoformat()),
                        (
                            "etsi:SigningCertificateV2",
                            (),
                            (
                                "etsi:Cert",
                                (),
                                (
                                    "etsi:CertDigest",
                                    (),
                                    (
                                        "ds:DigestMethod",
                                        (
                                            "Algorithm",
                                            "http://www.w3.org/2001/04/xmlenc#sha256",
                                        ),
                                    ),
                                    (
                                        "ds:DigestValue",
                                        (),
                                        b64encode(
                                            ctx.x509.fingerprint(hashes.SHA256())
                                        ).decode(),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "etsi:SignaturePolicyIdentifier",
                            (),
                            (
                                "etsi:SignaturePolicyId",
                                (),
                                (
                                    "etsi:SigPolicyId",
                                    (),
                                    ("etsi:Identifier", (), tax_agency.sign_file_url),
                                    (
                                        "etsi:Description",
                                        (),
                                    ),
                                ),
                                (
                                    "etsi:SigPolicyHash",
                                    (),
                                    (
                                        "ds:DigestMethod",
                                        (
                                            "Algorithm",
                                            "http://www.w3.org/2001/04/xmlenc#sha256",
                                        ),
                                    ),
                                    ("ds:DigestValue", (), tax_agency.sign_file_hash),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        root.append(signature)
        create_node_tree(signature, [dslist])
        ctx.sign(signature)
        signature_value = signature.find(
            "ds:SignatureValue", namespaces=xmlsig.constants.NS_MAP
        ).text
        # RFC2045 - Base64 Content-Transfer-Encoding (page 25)
        # Any characters outside of the base64 alphabet are to be ignored in
        # base64-encoded data.
        return signature_value.replace("\n", "")

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
            xml_element.text = value or ""

    def dict2xml(self, invoice_ordered_dict):
        tag = next(iter(invoice_ordered_dict))
        root = etree.Element(
            "{{{}}}{}".format(self.invoice_ns, tag), nsmap=self.invoice_nsmap
        )
        ticketbai_dict = invoice_ordered_dict.get(tag)
        for key, value in ticketbai_dict.items():
            self.create_node_from_dict(root, key, value)
        return root

    def parse_xml(self, xml):
        """
        Parse TicketBAI response XML
        :param xml: XML string
        :return: OrderedDict
        """
        namespaces = {self.invoice_ns: None}
        return xmltodict.parse(xml, process_namespaces=True, namespaces=namespaces)
