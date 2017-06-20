# -*- coding: utf-8 -*-
# © 2017 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from lxml import etree

import pytz
import random
import base64
import hashlib
import urllib2
import logging

try:
    import xmlsec
    from OpenSSL import crypto
except(ImportError, IOError) as err:
    logging.info(err)

from odoo import models, fields, tools, _, api
from odoo.exceptions import Warning as UserError, ValidationError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    correction_method = fields.Selection(
        selection=[
            ('01', 'Rectificación íntegra'),
            ('02', 'Rectificación por diferencias'),
            ('03', 'Rectificación por descuento por volumen de operaciones '
                   'durante un periodo'),
            ('04', 'Autorizadas por la Agencia Tributaria')
        ]
    )

    refund_reason = fields.Selection(
        selection=[
            ('01', 'Número de la factura'),
            ('02', 'Serie de la factura'),
            ('03', 'Fecha expedición'),
            ('04', 'Nombre y apellidos/Razón social - Emisor'),
            ('05', 'Nombre y apellidos/Razón social - Receptor'),
            ('06', 'Identificación fiscal Emisor/Obligado'),
            ('07', 'Identificación fiscal Receptor'),
            ('08', 'Domicilio Emisor/Obligado'),
            ('09', 'Domicilio Receptor'),
            ('10', 'Detalle Operación'),
            ('11', 'Porcentaje impositivo a aplicar'),
            ('12', 'Cuota tributaria a aplicar'),
            ('13', 'Fecha/Periodo a aplicar'),
            ('14', 'Clase de factura'),
            ('15', 'Literales legales'),
            ('16', 'Base imponible'),
            ('80', 'Cálculo de cuotas repercutidas'),
            ('81', 'Cálculo de cuotas retenidas'),
            ('82', 'Base imponible modificada por devolución de envases'
                   '/embalajes'),
            ('83', 'Base imponible modificada por descuentos y '
                   'bonificaciones'),
            ('84', 'Base imponible modificada por resolución firme, judicial '
                   'o administrativa'),
            ('85', 'Base imponible modificada cuotas repercutidas no '
                   'satisfechas. Auto de declaración de concurso')
        ]
    )

    integration_ids = fields.One2many(
        comodel_name='account.invoice.integration',
        inverse_name='invoice_id',
        copy=False
    )

    @api.depends('integration_ids')
    def _compute_integrations_count(self):
        self.integration_count = len(self.integration_ids)

    integration_count = fields.Integer(
        compute="_compute_integrations_count",
        string='# of Integrations', copy=False, default=0)

    @api.depends('integration_ids', 'partner_id')
    def _compute_can_integrate(self):
        for method in self.partner_id.invoice_integration_method_ids:
            if not self.env['account.invoice.integration'].search(
                    [('invoice_id', '=', self.id),
                     ('method_id', '=', method.id)]):
                self.can_integrate = True
                return
        self.can_integrate = False

    can_integrate = fields.Boolean(compute="_compute_can_integrate")

    @api.multi
    def action_integrations(self):
        self.ensure_one()
        for method in self.partner_id.invoice_integration_method_ids:
            if not self.env['account.invoice.integration'].search(
                    [('invoice_id', '=', self.id),
                     ('method_id', '=', method.id)]):
                method.create_integration(self)
        return self.action_view_integrations()

    @api.multi
    def action_view_integrations(self):
        self.ensure_one()
        action = self.env.ref(
            'l10n_es_facturae.invoice_integration_action')
        result = action.read()[0]
        result['context'] = {'default_invoice_id': self.id}
        integrations = self.env['account.invoice.integration'].search([
            ('invoice_id', '=', self.id)
        ])

        if len(integrations) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(integrations.ids) + \
                               ")]"
        elif len(integrations) == 1:
            res = self.env.ref('account.invoice.integration.form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = integrations.id
        return result

    def get_exchange_rate(self, euro_rate, currency_rate):
        if not euro_rate and not currency_rate:
            return fields.Datetime.now().strftime('%Y-%m-%d')
        if not currency_rate:
            return fields.Datetime.from_string(euro_rate.name
                                               ).strftime('%Y-%m-%d')
        if not euro_rate:
            return fields.Datetime.from_string(currency_rate.name
                                               ).strftime('%Y-%m-%d')
        currency_date = fields.Datetime.from_string(currency_rate.name)
        euro_date = fields.Datetime.from_string(currency_rate.name)
        if currency_date < euro_date:
            return currency_date.strftime('%Y-%m-%d')
        return euro_date.strftime('%Y-%m-%d')

    def get_refund_reason_string(self):
        return dict(
            self.fields_get(allfields=['refund_reason'])['refund_reason'][
                'selection'])[self.refund_reason]

    def get_correction_method_string(self):
        return dict(
            self.fields_get(allfields=['correction_method'])[
                'correction_method']['selection'])[self.correction_method]

    def validate_facturae_fields(self):
        if len(self.partner_id.vat) < 3:
            raise ValidationError(_('Partner vat is too small'))
        if len(self.company_id.vat) < 3:
            raise ValidationError(_('Company vat is too small'))
        if self.payment_mode_id.facturae_code == '02':
            if len(self.mandate_id.partner_bank_id.bank_id.bic) != 11:
                raise ValidationError(_('Mandate account BIC must be 11'))
            if len(self.mandate_id.partner_bank_id.acc_number) < 5:
                raise ValidationError(_('Mandate account is too small'))
        else:
            if self.partner_bank_id.bank_id.bic and len(
                    self.partner_bank_id.bank_id.bic) != 11:
                raise ValidationError(_('Selected account BIC must be 11'))
            if len(self.partner_bank_id.acc_number) < 5:
                raise ValidationError(_('Selected account is too small'))
        return

    def get_facturae(self, firmar_facturae):

        def _sign_file(cert, password, request):
            min = 1
            max = 99999
            signature_id = 'Signature%05d' % random.randint(min, max)
            signed_properties_id = signature_id + '-SignedProperties%05d' \
                                                  % random.randint(min, max)
            key_info_id = 'KeyInfo%05d' % random.randint(min, max)
            reference_id = 'Reference%05d' % random.randint(min, max)
            object_id = 'Object%05d' % random.randint(min, max)
            etsi = 'http://uri.etsi.org/01903/v1.3.2#'
            sig_policy_identifier = 'http://www.facturae.es/' \
                                    'politica_de_firma_formato_facturae/' \
                                    'politica_de_firma_formato_facturae_v3_1' \
                                    '.pdf'
            root = etree.fromstring(request)
            sign = xmlsec.template.create(
                root,
                c14n_method=xmlsec.constants.TransformInclC14N,
                sign_method=xmlsec.constants.TransformRsaSha1,
                name=signature_id,
                ns="ds"
            )
            key_info = xmlsec.template.ensure_key_info(
                sign,
                id=key_info_id
            )
            x509_data = xmlsec.template.add_x509_data(key_info)
            xmlsec.template.x509_data_add_certificate(x509_data)
            xmlsec.template.add_key_value(key_info)
            certificate = crypto.load_pkcs12(base64.b64decode(cert), password)
            certificate.set_ca_certificates(None)
            xmlsec.template.add_reference(
                sign,
                xmlsec.constants.TransformSha1,
                uri='#' + signed_properties_id,
                type='http://uri.etsi.org/01903#SignedProperties'
            )
            xmlsec.template.add_reference(
                sign,
                xmlsec.constants.TransformSha1,
                uri='#' + key_info_id
            )
            ref = xmlsec.template.add_reference(
                sign,
                xmlsec.constants.TransformSha1,
                uri="",
                id=reference_id
            )
            xmlsec.template.add_transform(
                ref,
                xmlsec.constants.TransformEnveloped
            )
            object_node = etree.SubElement(
                sign,
                etree.QName(xmlsec.constants.DSigNs, 'Object'),
                nsmap={'etsi': etsi},
                attrib={'Id': object_id}
            )
            qualifying_properties = etree.SubElement(
                object_node,
                etree.QName(etsi, 'QualifyingProperties'),
                attrib={
                    'Target': '#' + signature_id
                }
            )
            signed_properties = etree.SubElement(
                qualifying_properties,
                etree.QName(etsi, 'SignedProperties'),
                attrib={
                    'Id': signed_properties_id
                }
            )
            signed_signature_properties = etree.SubElement(
                signed_properties,
                etree.QName(etsi, 'SignedSignatureProperties')
            )
            now = datetime.now().replace(
                microsecond=0, tzinfo=pytz.utc
            )
            etree.SubElement(
                signed_signature_properties,
                etree.QName(etsi, 'SigningTime')
            ).text = now.isoformat()
            signing_certificate = etree.SubElement(
                signed_signature_properties,
                etree.QName(etsi, 'SigningCertificate')
            )
            signing_certificate_cert = etree.SubElement(
                signing_certificate,
                etree.QName(etsi, 'Cert')
            )
            cert_digest = etree.SubElement(
                signing_certificate_cert,
                etree.QName(etsi, 'CertDigest')
            )
            etree.SubElement(
                cert_digest,
                etree.QName(xmlsec.constants.DSigNs, 'DigestMethod'),
                attrib={
                    'Algorithm': 'http://www.w3.org/2000/09/xmldsig#sha1'
                }
            )
            hash_cert = hashlib.sha1(
                crypto.dump_certificate(
                    crypto.FILETYPE_ASN1,
                    certificate.get_certificate()
                )
            )
            etree.SubElement(
                cert_digest,
                etree.QName(xmlsec.constants.DSigNs, 'DigestValue')
            ).text = base64.b64encode(hash_cert.digest())
            issuer_serial = etree.SubElement(
                signing_certificate_cert,
                etree.QName(etsi, 'IssuerSerial')
            )
            issuer = ''
            comps = certificate.get_certificate().get_issuer().get_components()
            for entry in comps:
                issuer = entry[0] + '=' + entry[1] + (
                    (',' + issuer) if len(issuer) > 0 else ''
                )
            etree.SubElement(
                issuer_serial,
                etree.QName(xmlsec.constants.DSigNs, 'X509IssuerName')
            ).text = issuer
            etree.SubElement(
                issuer_serial,
                etree.QName(xmlsec.constants.DSigNs, 'X509SerialNumber')
            ).text = str(certificate.get_certificate().get_serial_number())
            signature_policy_identifier = etree.SubElement(
                signed_signature_properties,
                etree.QName(etsi, 'SignaturePolicyIdentifier')
            )
            signature_policy_id = etree.SubElement(
                signature_policy_identifier,
                etree.QName(etsi, 'SignaturePolicyId')
            )
            sig_policy_id = etree.SubElement(
                signature_policy_id,
                etree.QName(etsi, 'SigPolicyId')
            )
            etree.SubElement(
                sig_policy_id,
                etree.QName(etsi, 'Identifier')
            ).text = sig_policy_identifier
            etree.SubElement(
                sig_policy_id,
                etree.QName(etsi, 'Description')
            ).text = u"Política de Firma FacturaE v3.1"
            sig_policy_hash = etree.SubElement(
                signature_policy_id,
                etree.QName(etsi, 'SigPolicyHash')
            )
            etree.SubElement(
                sig_policy_hash,
                etree.QName(xmlsec.constants.DSigNs, 'DigestMethod'),
                attrib={
                    'Algorithm': 'http://www.w3.org/2000/09/xmldsig#sha1'
                }
            )
            remote = urllib2.urlopen(sig_policy_identifier)
            etree.SubElement(
                sig_policy_hash,
                etree.QName(xmlsec.constants.DSigNs, 'DigestValue')
            ).text = base64.b64encode(hashlib.sha1(remote.read()).digest())
            signer_role = etree.SubElement(
                signed_signature_properties,
                etree.QName(etsi, 'SignerRole')
            )
            claimed_roles = etree.SubElement(
                signer_role,
                etree.QName(etsi, 'ClaimedRoles')
            )
            etree.SubElement(
                claimed_roles,
                etree.QName(etsi, 'ClaimedRole')
            ).text = 'supplier'
            signed_data_object_properties = etree.SubElement(
                signed_properties,
                etree.QName(etsi, 'SignedDataObjectProperties')
            )
            data_object_format = etree.SubElement(
                signed_data_object_properties,
                etree.QName(etsi, 'DataObjectFormat'),
                attrib={
                    'ObjectReference': '#' + reference_id
                }
            )
            etree.SubElement(
                data_object_format,
                etree.QName(etsi, 'Description')
            ).text = 'Factura'
            etree.SubElement(
                data_object_format,
                etree.QName(etsi, 'MimeType')
            ).text = 'text/xml'
            ctx = xmlsec.SignatureContext()
            ctx.key = xmlsec.Key.from_memory(
                certificate.export(),
                format=xmlsec.constants.KeyDataFormatPkcs12
            )
            root.append(sign)
            ctx.sign(sign)
            return etree.tostring(
                root, xml_declaration=True, encoding='UTF-8'
            )

        logger = logging.getLogger("facturae")
        self.validate_facturae_fields()

        report = self.env.ref('l10n_es_facturae.report_facturae')
        xml_facturae = self.env['report'].get_html([self.id],
                                                   report.report_name)
        tree = etree.fromstring(
            xml_facturae, etree.XMLParser(remove_blank_text=True))
        xml_facturae = etree.tostring(tree, xml_declaration=True,
                                      encoding='UTF-8')
        self._validate_facturae(xml_facturae, logger)
        if self.company_id.facturae_cert and firmar_facturae:
            file_name = (_(
                'facturae') + '_' + self.number + '.xsig').replace('/', '-')
            invoice_file = _sign_file(
                self.company_id.facturae_cert,
                self.company_id.facturae_cert_password,
                xml_facturae)
        else:
            invoice_file = xml_facturae
            file_name = (_(
                'facturae') + '_' + self.number + '.xml').replace('/', '-')

        return invoice_file, file_name

    @staticmethod
    def _validate_facturae(xml_string, logger):
        facturae_schema = etree.XMLSchema(
            etree.parse(tools.file_open(
                "Facturaev3_2.xsd", subdir="addons/l10n_es_facturae/data")))
        try:
            facturae_schema.assertValid(etree.fromstring(xml_string))
        except Exception, e:
            logger.warning(
                "The XML file is invalid against the XML Schema Definition")
            logger.warning(xml_string)
            logger.warning(e)
            raise UserError(
                _("The generated XML file is not valid against the official "
                  "XML Schema Definition. The generated XML file and the "
                  "full error have been written in the server logs. Here "
                  "is the error, which may give you an idea on the cause "
                  "of the problem : %s") % unicode(e))
        return True
