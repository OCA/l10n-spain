# Copyright 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import hashlib
import logging
import random
from collections import defaultdict
from datetime import datetime

import pytz
from lxml import etree

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError, Warning as UserError

from odoo.addons.base.models.ir_ui_view import (
    transfer_modifiers_to_node,
    transfer_node_to_modifiers,
)

try:
    import xmlsig
    from OpenSSL import crypto
except (ImportError, IOError) as err:
    logging.info(err)


logger = logging.Logger("facturae")


class AccountMove(models.Model):
    _inherit = "account.move"

    facturae = fields.Boolean(compute="_compute_facturae")
    correction_method = fields.Selection(
        selection=[
            ("01", "Rectificación íntegra"),
            ("02", "Rectificación por diferencias"),
            (
                "03",
                "Rectificación por descuento por volumen de operaciones "
                "durante un periodo",
            ),
            ("04", "Autorizadas por la Agencia Tributaria"),
        ]
    )

    facturae_refund_reason = fields.Selection(
        selection=[
            ("01", "Número de la factura"),
            ("02", "Serie de la factura"),
            ("03", "Fecha expedición"),
            ("04", "Nombre y apellidos/Razón social - Emisor"),
            ("05", "Nombre y apellidos/Razón social - Receptor"),
            ("06", "Identificación fiscal Emisor/Obligado"),
            ("07", "Identificación fiscal Receptor"),
            ("08", "Domicilio Emisor/Obligado"),
            ("09", "Domicilio Receptor"),
            ("10", "Detalle Operación"),
            ("11", "Porcentaje impositivo a aplicar"),
            ("12", "Cuota tributaria a aplicar"),
            ("13", "Fecha/Periodo a aplicar"),
            ("14", "Clase de factura"),
            ("15", "Literales legales"),
            ("16", "Base imponible"),
            ("80", "Cálculo de cuotas repercutidas"),
            ("81", "Cálculo de cuotas retenidas"),
            ("82", "Base imponible modificada por devolución de envases" "/embalajes"),
            ("83", "Base imponible modificada por descuentos y " "bonificaciones"),
            (
                "84",
                "Base imponible modificada por resolución firme, judicial "
                "o administrativa",
            ),
            (
                "85",
                "Base imponible modificada cuotas repercutidas no "
                "satisfechas. Auto de declaración de concurso",
            ),
        ]
    )
    facturae_start_date = fields.Date(
        readonly=True, states={"draft": [("readonly", False)]},
    )
    facturae_end_date = fields.Date(
        readonly=True, states={"draft": [("readonly", False)]},
    )
    thirdparty_invoice = fields.Boolean(
        string="Third-party invoice",
        copy=False,
        compute="_compute_thirdparty_invoice",
        store=True,
        readonly=False,
    )
    thirdparty_number = fields.Char(
        string="Third-party number",
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
        help="Número de la factura emitida por un tercero.",
    )

    @api.depends("journal_id")
    def _compute_thirdparty_invoice(self):
        for item in self:
            item.thirdparty_invoice = item.journal_id.thirdparty_invoice

    @api.constrains("facturae_start_date", "facturae_end_date")
    def _check_facturae_date(self):
        for record in self:
            if bool(record.facturae_start_date) != bool(record.facturae_end_date):
                raise ValidationError(
                    _(
                        "FacturaE start and end dates are both required if one of "
                        "them is filled"
                    )
                )
            if (
                record.facturae_start_date
                and record.facturae_start_date > record.facturae_end_date
            ):
                raise ValidationError(_("Start date cannot be later than end date"))

    @api.depends("partner_id.facturae", "type")
    def _compute_facturae(self):
        for record in self:
            record.facturae = record.partner_id.facturae and record.type in [
                "out_invoice",
                "out_refund",
            ]

    def get_exchange_rate(self, euro_rate, currency_rate):
        if not euro_rate and not currency_rate:
            return fields.Datetime.now().strftime("%Y-%m-%d")
        if not currency_rate:
            return fields.Datetime.to_datetime(euro_rate.name).strftime("%Y-%m-%d")
        if not euro_rate:
            return fields.Datetime.to_datetime(currency_rate.name).strftime("%Y-%m-%d")
        currency_date = fields.Datetime.to_datetime(currency_rate.name)
        euro_date = fields.Datetime.to_datetime(currency_rate.name)
        if currency_date < euro_date:
            return currency_date.strftime("%Y-%m-%d")
        return euro_date.strftime("%Y-%m-%d")

    def get_refund_reason_string(self):
        return dict(
            self.fields_get(allfields=["facturae_refund_reason"])[
                "facturae_refund_reason"
            ]["selection"]
        )[self.facturae_refund_reason]

    def get_correction_method_string(self):
        return dict(
            self.fields_get(allfields=["correction_method"])["correction_method"][
                "selection"
            ]
        )[self.correction_method]

    def _get_valid_move_statuses(self):
        return ["posted"]

    def validate_facturae_fields(self):
        lines = self.line_ids.filtered(
            lambda r: not r.display_type and not r.exclude_from_invoice_tab
        )
        for line in lines:
            if not line.tax_ids:
                raise ValidationError(
                    _("Taxes not provided in move line " "%s") % line.name
                )
        if not self.partner_id.vat:
            raise ValidationError(_("Partner vat not provided"))
        if not self.company_id.partner_id.vat:
            raise ValidationError(_("Company vat not provided"))
        if len(self.partner_id.vat) < 3:
            raise ValidationError(_("Partner vat is too small"))
        if not self.partner_id.state_id:
            raise ValidationError(_("Partner state not provided"))
        if len(self.company_id.vat) < 3:
            raise ValidationError(_("Company vat is too small"))
        if not self.payment_mode_id:
            raise ValidationError(_("Payment mode is required"))
        if self.payment_mode_id.facturae_code:
            partner_bank = self.partner_banks_to_show()[:1]
            if (
                partner_bank
                and partner_bank.bank_id.bic
                and len(partner_bank.bank_id.bic) != 11
            ):
                raise ValidationError(_("Selected account BIC must be 11"))
            if partner_bank and len(partner_bank.acc_number) < 5:
                raise ValidationError(_("Selected account is too small"))
        if self.state not in self._get_valid_move_statuses():
            raise ValidationError(
                _(
                    "You can only create Factura-E files for "
                    "moves that have been validated."
                )
            )
        return

    def _get_facturae_move_attachments(self):
        result = []
        if self.partner_id.attach_invoice_as_annex:
            action = self.env.ref("account.account_invoices")
            content, content_type = action.render(self.ids)
            result.append(
                {
                    "data": base64.b64encode(content),
                    "content_type": content_type,
                    "encoding": "BASE64",
                    "description": _("Invoice %s") % self.name,
                    "compression": False,
                }
            )
        return result

    def get_facturae(self, firmar_facturae):
        def _sign_file(cert, password, request):
            rand_min = 1
            rand_max = 99999
            signature_id = "Signature%05d" % random.randint(rand_min, rand_max)
            signed_properties_id = (
                signature_id
                + "-SignedProperties%05d" % random.randint(rand_min, rand_max)
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
            certificate = crypto.load_pkcs12(base64.b64decode(cert), password)
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
            hash_cert = hashlib.sha1(
                crypto.dump_certificate(
                    crypto.FILETYPE_ASN1, certificate.get_certificate()
                )
            )
            etree.SubElement(
                cert_digest, etree.QName(xmlsig.constants.DSigNs, "DigestValue")
            ).text = base64.b64encode(hash_cert.digest())
            issuer_serial = etree.SubElement(
                signing_certificate_cert, etree.QName(etsi, "IssuerSerial")
            )
            etree.SubElement(
                issuer_serial, etree.QName(xmlsig.constants.DSigNs, "X509IssuerName")
            ).text = xmlsig.utils.get_rdns_name(
                certificate.get_certificate().to_cryptography().issuer.rdns
            )
            etree.SubElement(
                issuer_serial, etree.QName(xmlsig.constants.DSigNs, "X509SerialNumber")
            ).text = str(certificate.get_certificate().get_serial_number())
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
            ).text = "Política de Firma FacturaE v3.1"
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
            claimed_roles = etree.SubElement(
                signer_role, etree.QName(etsi, "ClaimedRoles")
            )
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
            key = crypto.load_pkcs12(base64.b64decode(cert), password)
            ctx.x509 = key.get_certificate().to_cryptography()
            ctx.public_key = ctx.x509.public_key()
            ctx.private_key = key.get_privatekey().to_cryptography_key()
            root.append(sign)
            ctx.sign(sign)
            return etree.tostring(root, xml_declaration=True, encoding="UTF-8")

        self.validate_facturae_fields()

        report = self.env.ref("l10n_es_facturae.report_facturae")
        xml_facturae = report.render_qweb_xml(self.ids, {})[0]
        # Quitamos espacios en blanco, para asegurar que el XML final quede
        # totalmente libre de ellos.
        tree = etree.fromstring(xml_facturae, etree.XMLParser(remove_blank_text=True))
        xml_facturae = etree.tostring(tree, xml_declaration=True, encoding="UTF-8")
        self._validate_facturae(xml_facturae)
        if self.company_id.facturae_cert and firmar_facturae:
            file_name = (_("facturae") + "_" + self.name + ".xsig").replace("/", "-")
            move_file = _sign_file(
                self.company_id.facturae_cert,
                self.company_id.facturae_cert_password,
                xml_facturae,
            )
        else:
            move_file = xml_facturae
            file_name = (_("facturae") + "_" + self.name + ".xml").replace("/", "-")

        return move_file, file_name

    def get_facturae_version(self):
        return (
            self.partner_id.facturae_version
            or self.company_id.facturae_version
            or "3_2"
        )

    def _get_facturae_schema_file(self):
        return tools.file_open(
            "Facturaev%s.xsd" % self.get_facturae_version(),
            subdir="addons/l10n_es_facturae/data",
        )

    def _validate_facturae(self, xml_string):
        facturae_schema = etree.XMLSchema(etree.parse(self._get_facturae_schema_file()))
        try:

            facturae_schema.assertValid(etree.fromstring(xml_string))
        except Exception as e:
            logger.warning("The XML file is invalid against the XML Schema Definition")
            logger.warning(xml_string)
            logger.warning(e)
            raise UserError(
                _(
                    "The generated XML file is not valid against the official "
                    "XML Schema Definition. The generated XML file and the "
                    "full error have been written in the server logs. Here "
                    "is the error, which may give you an idea on the cause "
                    "of the problem : %s"
                )
                % str(e)
            )
        return True

    def _get_facturae_tax_info(self):
        self.ensure_one()
        output_taxes = defaultdict(lambda: {"base": 0, "amount": 0})
        withheld_taxes = defaultdict(lambda: {"base": 0, "amount": 0})
        for line in self.line_ids:
            sign = -1 if self.type[:3] == "out" else 1
            for tax in line.tax_ids:
                if tools.float_compare(tax.amount, 0, precision_digits=2) >= 0:
                    output_taxes[tax]["base"] += line.balance * sign
                else:
                    withheld_taxes[tax]["base"] += line.balance * sign
        for tax in output_taxes:
            output_taxes[tax]["amount"] = output_taxes[tax]["base"] * tax.amount / 100
        for tax in withheld_taxes:
            withheld_taxes[tax]["amount"] = (
                withheld_taxes[tax]["base"] * tax.amount / 100
            )
        return output_taxes, withheld_taxes

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        """Thirdparty fields are added to the form view only if they don't exist."""
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu,
        )
        if view_type == "form":
            doc = etree.XML(res["arch"])
            node = doc.xpath("//field[@name='thirdparty_invoice']")
            if node:
                return res
            for node in doc.xpath("//field[@name='ref']"):
                attrs = {
                    "required": [("thirdparty_invoice", "=", True)],
                    "invisible": [("thirdparty_invoice", "=", False)],
                }
                elem = etree.Element(
                    "field", {"name": "thirdparty_number", "attrs": str(attrs)},
                )
                modifiers = {}
                transfer_node_to_modifiers(elem, modifiers)
                transfer_modifiers_to_node(modifiers, elem)
                node.addnext(elem)
                res["fields"].update(self.fields_get(["thirdparty_number"]))
                attrs = {
                    "invisible": [
                        (
                            "type",
                            "not in",
                            ("in_invoice", "out_invoice", "out_refund", "in_refund"),
                        )
                    ],
                }
                elem = etree.Element(
                    "field", {"name": "thirdparty_invoice", "attrs": str(attrs)}
                )
                transfer_node_to_modifiers(elem, modifiers)
                transfer_modifiers_to_node(modifiers, elem)
                node.addnext(elem)
                res["fields"].update(self.fields_get(["thirdparty_invoice"]))
            res["arch"] = etree.tostring(doc)
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    facturae_receiver_contract_reference = fields.Char()
    facturae_receiver_contract_date = fields.Date()
    facturae_receiver_transaction_reference = fields.Char()
    facturae_receiver_transaction_date = fields.Date()
    facturae_issuer_contract_reference = fields.Char()
    facturae_issuer_contract_date = fields.Date()
    facturae_issuer_transaction_reference = fields.Char()
    facturae_issuer_transaction_date = fields.Date()
    facturae_file_reference = fields.Char()
    facturae_file_date = fields.Date()
    facturae_start_date = fields.Date()
    facturae_end_date = fields.Date()
    facturae_transaction_date = fields.Date()

    @api.constrains("facturae_start_date", "facturae_end_date")
    def _check_facturae_date(self):
        for record in self:
            if bool(record.facturae_start_date) != bool(record.facturae_end_date):
                raise ValidationError(
                    _(
                        "FacturaE start and end dates are both required if one of "
                        "them is filled"
                    )
                )
            if (
                record.facturae_start_date
                and record.facturae_start_date > record.facturae_end_date
            ):
                raise ValidationError(_("Start date cannot be later than end date"))

    def button_edit_facturae_fields(self):
        self.ensure_one()
        view = self.env.ref("l10n_es_facturae.view_facturae_fields")
        return {
            "name": _("Facturae Configuration"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": self._name,
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
            "context": self.env.context,
        }
