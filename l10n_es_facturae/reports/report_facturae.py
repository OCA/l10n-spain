# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import hashlib
import logging
import random
from datetime import datetime

import pytz
import xmlsig
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import Encoding
from lxml import etree

from odoo import _, api, models, tools
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ReportFacturae(models.AbstractModel):
    _name = "report.l10n_es_facturae.facturae_signed"
    _inherit = "report.report_xml.abstract"
    _description = "Account Move Facturae Signed"

    def _get_report_values(self, docids, data=None):
        result = super(ReportFacturae, self)._get_report_values(docids, data=data)
        result["docs"] = self.env["account.move"].browse(docids)
        return result

    @api.model
    def generate_report(self, ir_report, docids, data=None):
        move = self.env["account.move"].browse(docids)
        move.ensure_one()
        move.validate_facturae_fields()
        xml_facturae, content_type = super().generate_report(
            ir_report, docids, data=data
        )
        # Quitamos espacios en blanco, para asegurar que el XML final quede
        # totalmente libre de ellos.
        tree = etree.fromstring(xml_facturae, etree.XMLParser(remove_blank_text=True))
        xml_facturae = etree.tostring(tree, xml_declaration=True, encoding="UTF-8")
        self._validate_facturae(move, xml_facturae)
        public_crt, private_key = (
            self.env["l10n.es.aeat.certificate"]
            .sudo()
            .get_certificates(move.company_id)
        )
        move_file = self._sign_file(move, xml_facturae, public_crt, private_key)
        return move_file, content_type

    def _get_facturae_schema_file(self, move):
        return tools.file_open(
            "addons/l10n_es_facturae/data/Facturaev%s.xsd"
            % move.get_facturae_version(),
        )

    def _validate_facturae(self, move, xml_string):
        facturae_schema = etree.XMLSchema(
            etree.parse(self._get_facturae_schema_file(move))
        )
        try:

            facturae_schema.assertValid(etree.fromstring(xml_string))
        except Exception as e:
            _logger.warning("The XML file is invalid against the XML Schema Definition")
            _logger.warning(xml_string)
            _logger.warning(e)
            raise UserError(
                _(
                    "The generated XML file is not valid against the official "
                    "XML Schema Definition. The generated XML file and the "
                    "full error have been written in the server logs. Here "
                    "is the error, which may give you an idea on the cause "
                    "of the problem : %s"
                )
                % str(e)
            ) from e
        return True

    def _sign_file(self, move, request, public_cert, private_key):
        rand_min = 1
        rand_max = 99999
        signature_id = "Signature%05d" % random.randint(rand_min, rand_max)
        signed_properties_id = signature_id + "-SignedProperties%05d" % random.randint(
            rand_min, rand_max
        )
        key_info_id = "KeyInfo%05d" % random.randint(rand_min, rand_max)
        reference_id = "Reference%05d" % random.randint(rand_min, rand_max)
        object_id = "Object%05d" % random.randint(rand_min, rand_max)
        etsi = "http://uri.etsi.org/01903/v1.3.2#"
        sig_policy_identifier = (
            "http://www.facturae.es/"
            "politica_de_firma_formato_facturae/"
            "politica_de_firma_formato_facturae_v3_1"
            ".pdf"
        )
        sig_policy_hash_value = "Ohixl6upD6av8N7pEvDABhEL6hM="
        root = etree.fromstring(request)
        sign = xmlsig.template.create(
            c14n_method=xmlsig.constants.TransformInclC14N,
            sign_method=xmlsig.constants.TransformRsaSha1,
            name=signature_id,
            ns="ds",
        )
        key_info = xmlsig.template.ensure_key_info(sign, name=key_info_id)
        x509_data = xmlsig.template.add_x509_data(key_info)
        xmlsig.template.x509_data_add_certificate(x509_data)
        xmlsig.template.add_key_value(key_info)
        try:
            with open(public_cert, "rb") as f:
                certificate = x509.load_pem_x509_certificate(
                    f.read(), backend=default_backend()
                )
        except FileNotFoundError as e:
            raise ValidationError(
                _("The provided certificate is not found in the system.")
            ) from e
        xmlsig.template.add_reference(
            sign,
            xmlsig.constants.TransformSha1,
            uri="#" + signed_properties_id,
            uri_type="http://uri.etsi.org/01903#SignedProperties",
        )
        xmlsig.template.add_reference(
            sign, xmlsig.constants.TransformSha1, uri="#" + key_info_id
        )
        ref = xmlsig.template.add_reference(
            sign, xmlsig.constants.TransformSha1, name=reference_id, uri=""
        )
        xmlsig.template.add_transform(ref, xmlsig.constants.TransformEnveloped)
        object_node = etree.SubElement(
            sign,
            etree.QName(xmlsig.constants.DSigNs, "Object"),
            nsmap={"etsi": etsi},
            attrib={xmlsig.constants.ID_ATTR: object_id},
        )
        qualifying_properties = etree.SubElement(
            object_node,
            etree.QName(etsi, "QualifyingProperties"),
            attrib={"Target": "#" + signature_id},
        )
        signed_properties = etree.SubElement(
            qualifying_properties,
            etree.QName(etsi, "SignedProperties"),
            attrib={xmlsig.constants.ID_ATTR: signed_properties_id},
        )
        signed_signature_properties = etree.SubElement(
            signed_properties, etree.QName(etsi, "SignedSignatureProperties")
        )
        now = datetime.now().replace(microsecond=0, tzinfo=pytz.utc)
        etree.SubElement(
            signed_signature_properties, etree.QName(etsi, "SigningTime")
        ).text = now.isoformat()
        signing_certificate = etree.SubElement(
            signed_signature_properties, etree.QName(etsi, "SigningCertificate")
        )
        signing_certificate_cert = etree.SubElement(
            signing_certificate, etree.QName(etsi, "Cert")
        )
        cert_digest = etree.SubElement(
            signing_certificate_cert, etree.QName(etsi, "CertDigest")
        )
        etree.SubElement(
            cert_digest,
            etree.QName(xmlsig.constants.DSigNs, "DigestMethod"),
            attrib={"Algorithm": "http://www.w3.org/2000/09/xmldsig#sha1"},
        )
        hash_cert = hashlib.sha1(certificate.public_bytes(Encoding.DER))
        etree.SubElement(
            cert_digest, etree.QName(xmlsig.constants.DSigNs, "DigestValue")
        ).text = base64.b64encode(hash_cert.digest())
        issuer_serial = etree.SubElement(
            signing_certificate_cert, etree.QName(etsi, "IssuerSerial")
        )
        etree.SubElement(
            issuer_serial, etree.QName(xmlsig.constants.DSigNs, "X509IssuerName")
        ).text = xmlsig.utils.get_rdns_name(certificate.issuer.rdns)
        etree.SubElement(
            issuer_serial, etree.QName(xmlsig.constants.DSigNs, "X509SerialNumber")
        ).text = str(certificate.serial_number)
        signature_policy_identifier = etree.SubElement(
            signed_signature_properties,
            etree.QName(etsi, "SignaturePolicyIdentifier"),
        )
        signature_policy_id = etree.SubElement(
            signature_policy_identifier, etree.QName(etsi, "SignaturePolicyId")
        )
        sig_policy_id = etree.SubElement(
            signature_policy_id, etree.QName(etsi, "SigPolicyId")
        )
        etree.SubElement(
            sig_policy_id, etree.QName(etsi, "Identifier")
        ).text = sig_policy_identifier
        etree.SubElement(
            sig_policy_id, etree.QName(etsi, "Description")
        ).text = "Política de Firma Facturae v3.1"
        sig_policy_hash = etree.SubElement(
            signature_policy_id, etree.QName(etsi, "SigPolicyHash")
        )
        etree.SubElement(
            sig_policy_hash,
            etree.QName(xmlsig.constants.DSigNs, "DigestMethod"),
            attrib={"Algorithm": "http://www.w3.org/2000/09/xmldsig#sha1"},
        )
        hash_value = sig_policy_hash_value
        etree.SubElement(
            sig_policy_hash, etree.QName(xmlsig.constants.DSigNs, "DigestValue")
        ).text = hash_value
        signer_role = etree.SubElement(
            signed_signature_properties, etree.QName(etsi, "SignerRole")
        )
        claimed_roles = etree.SubElement(signer_role, etree.QName(etsi, "ClaimedRoles"))
        etree.SubElement(
            claimed_roles, etree.QName(etsi, "ClaimedRole")
        ).text = "supplier"
        signed_data_object_properties = etree.SubElement(
            signed_properties, etree.QName(etsi, "SignedDataObjectProperties")
        )
        data_object_format = etree.SubElement(
            signed_data_object_properties,
            etree.QName(etsi, "DataObjectFormat"),
            attrib={"ObjectReference": "#" + reference_id},
        )
        etree.SubElement(
            data_object_format, etree.QName(etsi, "Description")
        ).text = "Factura"
        etree.SubElement(
            data_object_format, etree.QName(etsi, "MimeType")
        ).text = "text/xml"
        ctx = xmlsig.SignatureContext()

        ctx.x509 = certificate
        ctx.public_key = certificate.public_key()
        with open(private_key, "rb") as f:
            ctx.private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )
        root.append(sign)
        ctx.sign(sign)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8")
