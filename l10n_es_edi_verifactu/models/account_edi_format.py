# -*- coding: utf-8 -*-
# Copyright 2024 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import copy
import json
import requests
from base64 import b64encode
from datetime import datetime
from markupsafe import Markup
from lxml import etree
from odoo import models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons.l10n_es_edi_sii.models.account_edi_format import PatchedHTTPAdapter
from ..lib.verifactu_xmlgen import verifactu_xmlgen
from ..lib.verifactu_xmlgen import OPERATION_CREATE, OPERATION_CANCEL

AEAT_VERIFACTU_URL = """ 
"""

VERIFACTU_XML_BASE = """
<soapenv:Envelope
    xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:sum="https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd"
    xmlns:sum1="https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd">
    <soapenv:Header/>
    <soapenv:Body>
        <sum:RegFactuSistemaFacturacion>
            <sum1:Cabecera>
                <sum1:ObligadoEmision>
                    <sum1:NombreRazon/>
                    <sum1:NIF/>
                </sum1:ObligadoEmision>
            </sum1:Cabecera>
            <sum:RegistroFactura/>
        </sum:RegFactuSistemaFacturacion>
    </soapenv:Body>
</soapenv:Envelope>
""".encode(
    "utf-8"
)


class AccountEdiFormat(models.Model):
    _inherit = "account.edi.format"

    def _l10n_es_edi_verifactu_content(self, invoice):
        cancel = invoice.edi_state in ("to_cancel", "cancelled")
        xml_tree = self._l10n_es_verifactu_get_xml(invoice, cancel)
        xml_str = etree.tostring(xml_tree)
        return xml_str

    def _l10n_es_edi_verifactu_post_invoice(self, invoice):
        if self.code != "es_verifactu":
            return super()._post_invoice_edi(invoice)
        # TODO chain integrity check ¿?
        # Call the web service and get response
        res = self._l10n_es_verifactu_post_to_web_service(invoice)
        if res[invoice].get("success"):
            # Create attachment, post and save as EDI DOC
            attachment = self.env["ir.attachment"].create(
                {
                    "name": invoice.name + "_verifactu_post.xml",
                    "datas": invoice.l10n_es_edi_verifactu_xml,
                    "mimetype": "application/xml",
                    "res_id": invoice.id,
                    "res_model": "account.move",
                }
            )
            test_suffix = (
                "(test mode)" if invoice.company_id.l10n_es_edi_test_env else ""
            )
            # TODO message XXX
            invoice.with_context(no_new_invoice=True).message_post(
                body=Markup(
                    "<pre>Verifactu: posted emission XML {test_suffix}\n{message}</pre>"
                ).format(test_suffix=test_suffix, message="XXX"),
                attachment_ids=[attachment.id],
            )
            res[invoice]["attachment"] = attachment
        else:
            # TODO error management
            pass
        return res

    def _l10n_es_edi_verifactu_cancel_invoice(self, invoice):
        # TODO cancellation of invoices
        raise NotImplementedError("")

    def _l10n_es_verifactu_get_xml(self, invoice, cancel=False):
        """l10n_es_edi_verifactu: generates the XML"""
        # If previously generated XML reuse it
        xml_root_node = invoice.get_l10n_es_edi_verifactu_xml(cancel)
        if xml_root_node is not None:
            return xml_root_node
        # Otherwise, generate a new XML
        errors = self._ensure_verifactu_software_settings(
            invoice
        ) + self._ensure_verifactu_invoice_data(invoice)
        if errors:
            raise UserError(
                _("Invalid invoice configuration:\n\n%s") % "\n".join(errors)
            )
        invoice_records_xml = self.cmd_get_verifactu_xml(invoice)
        root_records = etree.fromstring(invoice_records_xml)
        xml_root_node = etree.fromstring(VERIFACTU_XML_BASE)
        issuer_name_node = xml_root_node.xpath(
            ".//sum1:NombreRazon", namespaces=xml_root_node.nsmap
        )[0]
        issuer_name_node.text = invoice.company_id.name[:120]
        issuer_vat_node = xml_root_node.xpath(
            ".//sum1:NIF", namespaces=xml_root_node.nsmap
        )[0]
        issuer_vat_node.text = (
            invoice.company_id.vat[2:]
            if invoice.company_id.vat.startswith("ES")
            else invoice.company_id.vat
        )
        records_node = xml_root_node.xpath(
            ".//sum:RegistroFactura", namespaces=xml_root_node.nsmap
        )[0]
        for child_node in root_records:
            records_node.append(copy.deepcopy(child_node))
        return xml_root_node

    def _l10n_es_verifactu_post_to_web_service(self, invoice):
        # TODO post to verifactu systems, not available yet
        # try:
        #     session = requests.Session()
        #     session.cert = invoice.company_id.l10n_es_edi_certificate_id
        #     session.mount("https://", PatchedHTTPAdapter())
        #     headers = {"Content-Type": "text/xml; charset=utf-8"}
        #     data = etree.tostring(
        #         invoice.get_l10n_es_edi_verifactu_xml(), encoding="UTF-8"
        #     )
        #     res = session.request(
        #         "post", AEAT_VERIFACTU_URL, data=data, headers=headers
        #     )
        # except (ValueError, requests.exceptions.RequestException) as e:
        #     return {
        #         invoice: {
        #             "error": str(e),
        #             "blocking_level": "warning",
        #             "response": None,
        #         }
        #     }
        return {
            invoice: {
                "success": True,
                "message": "XXX",
                "response": "XXX",
            }
        }

    @staticmethod
    def _get_verifactu_issuer(invoice):
        return {
            "irsId": invoice.company_id.vat[2:]
            if invoice.company_id.vat.startswith("ES")
            else invoice.company_id.vat,
            "name": invoice.company_id.name,
        }

    @staticmethod
    def _get_verifactu_invoice_id(invoice, cancel=False):
        issued_time = datetime.now().isoformat()
        if cancel:
            xml_issued_time = invoice.get_verifactu_issued_time_from_xml()
            if xml_issued_time:
                issued_time = datetime.strptime(xml_issued_time, "%d-%m-%Y").strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
        return {
            "number": invoice.name[:60],
            "issuedTime": issued_time,
        }

    @staticmethod
    def _get_verifactu_recipient(partner_id, partner_info):
        recipient = {
            "name": partner_id.name[:120],
            "country": partner_id.country_id.code,
        }
        if partner_id.country_id.code == "ES":
            recipient["irsId"] = partner_info.get("NIF")
        else:
            recipient["id"] = partner_info.get("IDOtro").get("ID")
            recipient["idType"] = partner_info.get("IDOtro").get("IDType")
        return recipient

    @staticmethod
    def _get_verifactu_description(invoice):
        return {
            "text": invoice.invoice_origin or "/",
            "operationDate": invoice.invoice_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    @staticmethod
    def _get_verifactu_invoice_type(invoice):
        simplified_partner = invoice.env.ref("l10n_es_edi_sii.partner_simplified")
        is_simplified = invoice.partner_id == simplified_partner
        if invoice.move_type == "out_invoice":
            return "F2" if is_simplified else "F1"
        elif invoice.move_type == "out_refund":
            return "R5" if is_simplified else "R1"
        else:
            return ""

    @staticmethod
    def _get_verifactu_es_vat_lines(vat_breakdown):
        subject_lines = []
        no_subject_lines = []
        subject_breakdown = vat_breakdown.get("DesgloseFactura").get("Sujeta", False)
        no_subject_breakdown = vat_breakdown.get("DesgloseFactura").get(
            "NoSujeta", False
        )
        tax_amount = 0
        if subject_breakdown:
            if subject_breakdown.get("NoExenta", False):
                tax_details = (
                    subject_breakdown.get("NoExenta")
                    .get("DesgloseIVA")
                    .get("DetalleIVA")
                )
                for tax_detail in tax_details:
                    subject_lines.append(
                        {
                            "base": tax_detail.get("BaseImponible"),
                            "rate": tax_detail.get("TipoImpositivo"),
                            "amount": tax_detail.get("CuotaRepercutida"),
                            "vatOperation": subject_breakdown.get("NoExenta").get(
                                "TipoNoExenta"
                            ),
                            "vatKey": "01",
                        }
                    )
                    tax_amount += tax_detail.get("CuotaRepercutida")
            if subject_breakdown.get("Exenta", False):
                tax_details = subject_breakdown.get("Exenta").get("DetalleExenta")
                for tax_detail in tax_details:
                    subject_lines.append(
                        {
                            "base": tax_detail.get("BaseImponible"),
                            "rate": 0,
                            "vatOperation": tax_detail.get("CausaExencion"),
                            "vatKey": "01",
                        }
                    )
        if no_subject_breakdown:
            not_subject_rl = no_subject_breakdown.get(
                "ImporteTAIReglasLocalizacion", False
            )
            not_subject_ot = no_subject_breakdown.get(
                "ImportePorArticulos7_14_Otros", False
            )
            if not_subject_rl:
                no_subject_lines.append(
                    {
                        "base": not_subject_rl,
                        "rate": 0,
                        # Spanish customer and tax is not subjet because of reglas de localización,
                        # so it should be a sale to Canarias, Ceuta or Melilla 08 vat key
                        "vatKey": "08",
                        "vatOperation": "N2",
                    }
                )
            if not_subject_ot:
                no_subject_lines.append(
                    {
                        "base": not_subject_ot,
                        "rate": 0,
                        "vatKey": "01",
                        "vatOperation": "N1",
                    }
                )
        return tax_amount, subject_lines + no_subject_lines

    @staticmethod
    def _get_verifactu_eu_extra_com_vat_lines(vat_breakdown):
        raise NotImplementedError()

    @api.model
    def _get_verifactu_vat_lines(self, invoice, vat_breakdown):
        if invoice.commercial_partner_id.country_id.code == "ES":
            return self._get_verifactu_es_vat_lines(vat_breakdown)
        else:
            return self._get_verifactu_eu_extra_com_vat_lines(vat_breakdown)

    @staticmethod
    def _get_verifactu_previous_id(previous_invoice):
        previous_issuer_id = previous_invoice.get_verifactu_issuer_vat_from_xml() or ""
        previous_issued_time = ""
        xml_issued_time = previous_invoice.get_verifactu_issued_time_from_xml()
        if xml_issued_time:
            previous_issued_time = datetime.strptime(
                xml_issued_time, "%d-%m-%Y"
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
        previous_hash = previous_invoice.get_verifactu_hash_from_xml() or ""
        return {
            "number": previous_invoice.name,
            "issuerIrsId": previous_issuer_id,
            "issuedTime": previous_issued_time,
            "hash": previous_hash,
        }

    def _attach_verifactu_xmlgen_json_input(self, attach_datas, invoice, cancel=False):
        attach_name = (
            invoice.name + "_verifactu_xmlgen.json"
            if not cancel
            else invoice.name + "_cancel_verifactu_xmlgen.json"
        )
        self.env["ir.attachment"].search(
            [("name", "=", attach_name), ("res_model", "=", "account.move")]
        ).unlink()
        attachment = self.env["ir.attachment"].create(
            {
                "name": attach_name,
                "datas": b64encode(json.dumps(attach_datas, indent=4).encode("UTF-8")),
                "mimetype": "application/json",
                "res_id": invoice.id,
                "res_model": "account.move",
            }
        )
        invoice.with_context(no_new_invoice=True).message_post(
            body="verifactu-xml json:", attachment_ids=[attachment.id]
        )

    @api.model
    def verifactu_xmlgen_prepare_json(self, invoice, cancel=False, attach=False):
        if invoice and not cancel:
            json_input = {
                "invoice": {
                    "issuer": self._get_verifactu_issuer(invoice),
                    "recipient": self._get_verifactu_recipient(
                        invoice.commercial_partner_id,
                        self._l10n_es_edi_get_partner_info(
                            invoice.commercial_partner_id
                        ),
                    ),
                    "id": self._get_verifactu_invoice_id(invoice, cancel),
                    "description": self._get_verifactu_description(invoice),
                    "type": self._get_verifactu_invoice_type(invoice),
                }
            }
            invoice_info_list = self._l10n_es_edi_get_invoices_info(invoice)
            if invoice_info_list:
                edi_sii_invoice_node = self._l10n_es_edi_get_invoices_info(invoice)[
                    0
                ].get("FacturaExpedida")
                tax_amount, vat_lines = self._get_verifactu_vat_lines(
                    invoice, edi_sii_invoice_node.get("TipoDesglose")
                )
                json_input["invoice"]["vatLines"] = vat_lines
                json_input["invoice"]["total"] = edi_sii_invoice_node.get(
                    "ImporteTotal"
                )
                json_input["invoice"]["amount"] = tax_amount
            previous_invoice = (
                invoice.company_id.get_l10n_es_verifactu_last_posted_invoice()
            )
            if previous_invoice:
                json_input["previousId"] = self._get_verifactu_previous_id(
                    previous_invoice
                )
            if attach:
                self._attach_verifactu_xmlgen_json_input(json_input, invoice)
            return json_input
        elif invoice and cancel:
            # TODO invoice cancellation
            raise NotImplementedError(_("Verifactu: invoice cancel not supported yet."))
        else:
            raise ValidationError(_("Verifactu: invoice needed."))

    @api.model
    def cmd_get_verifactu_xml(self, invoice, cancel=False):
        json_input = self.verifactu_xmlgen_prepare_json(
            invoice, cancel=cancel, attach=True
        )
        process = verifactu_xmlgen(
            OPERATION_CANCEL if cancel else OPERATION_CREATE,
            json.dumps(json_input),
            self.env,
            invoice.company_id,
        )
        if process.returncode != 0:
            err_msgs = (
                process.stderr.decode("utf-8").split("\n") if process.stderr else []
            )
            validation_error = err_msgs[0] if len(err_msgs) > 0 else ""
            if len(err_msgs) > 2:
                code = err_msgs[1]
                validation_error = "Verifactu verifactu-xmlgen: [%s] %s" % (
                    code,
                    validation_error,
                )
                validation_error += "\n" + json.dumps(json_input, indent=4)
            raise ValidationError(validation_error)
        json_result = json.loads(process.stdout)
        return base64.b64decode(json_result["verifactuXml"])

    # -------------------------------------------------------------------------
    # EDI OVERRIDDEN METHODS
    # -------------------------------------------------------------------------

    def _get_move_applicability(self, move):
        self.ensure_one()
        if self.code != "es_verifactu":
            return super()._get_move_applicability(move)
        if move.l10n_es_edi_verifactu_is_required:
            return {
                "post": self._l10n_es_edi_verifactu_post_invoice,
                "cancel": self._l10n_es_edi_verifactu_cancel_invoice,
                # TODO post_batching is needed in case of t waiting time or n number invoices to wait in the response
                # 'post_batching': lambda invoice: (invoice.move_type, invoice.l10n_es_edi_csv),
                "edi_content": self._l10n_es_edi_verifactu_content,
            }

    @staticmethod
    def _ensure_verifactu_software_settings(invoice):
        errors = []
        license_data = invoice.company_id.get_l10n_es_verifactu_license_dict()
        developer_id = license_data.get("developer_id", False)
        software_id = license_data.get("software_id", False)
        software_name = license_data.get("software_name", False)
        software_number = license_data.get("software_number", False)
        software_version = license_data.get("software_version", False)
        software_settings = (
            developer_id
            and software_id
            and software_name
            and software_number
            and software_version
        )
        if not software_settings:
            errors.append(
                _("Verifactu: please configure all software data in general settings.")
            )
        return errors

    @staticmethod
    def _ensure_verifactu_invoice_data(invoice):
        errors = []
        if not invoice.company_id.vat:
            errors.append(
                _(
                    "VAT number is missing on company %s",
                    invoice.company_id.display_name,
                )
            )
        if not invoice.partner_id.country_id:
            errors.append(
                _("Country is missing on partner %s", invoice.partner_id.name)
            )
        return errors

    @staticmethod
    def _ensure_verifactu_supported_invoice(invoice):
        # TODO Not supported invoices that actually we should support
        # 1. Non Spanish customers
        if not invoice.partner_id.country_id.code == "ES":
            raise ValidationError(
                _("Verifactu: non Spanish customer invoices are not supported.")
            )
        # 2. Refund invoices
        if invoice.move_type == "out_refund":
            raise ValidationError(_("Verifactu: refund invoices are not supported."))
        # 3. Simplified invoices
        simplified_partner = invoice.env.ref("l10n_es_edi_sii.partner_simplified")
        is_simplified = invoice.partner_id == simplified_partner
        if is_simplified:
            raise ValidationError(
                _("Verifactu: simplified invoices are not supported.")
            )
        # 4. Non supported tax
        supported_taxes = ["exento", "sujeto", "no_sujeto", "no_sujeto_loc", "ignore"]
        if any(
            tax
            for tax in invoice.invoice_line_ids.tax_ids.filtered(
                lambda tax: tax.l10n_es_type not in supported_taxes
            )
        ):
            raise ValidationError(_("Verifactu: not supported invoice taxes."))
        return True

    def _check_move_configuration(self, invoice):
        errors = super()._check_move_configuration(invoice)
        if self.code != "es_verifactu" or invoice.country_code != "ES":
            return errors
        errors += self._ensure_verifactu_software_settings(invoice)
        errors += self._ensure_verifactu_invoice_data(invoice)
        if not errors and self.env.context.get("l10n_es_verifactu_get_xml", False):
            self._ensure_verifactu_supported_invoice(invoice)
            verifactu_xml = self._l10n_es_verifactu_get_xml(invoice)
            invoice.update_l10n_es_edi_verifactu_xml(verifactu_xml, False)
            # Assign unique 'chain index' from dedicated sequence
            if not invoice.l10n_es_edi_verifactu_chain_index:
                invoice.l10n_es_edi_verifactu_chain_index = (
                    invoice.company_id.get_l10n_es_verifactu_next_chain_index()
                )
        return errors

    def _needs_web_services(self):
        return self.code == "es_verifactu" or super()._needs_web_services()

    def _is_enabled_by_default_on_journal(self, journal):
        """Disable SII by default on a new journal when verifactu is installed"""
        if self.code != "es_sii":
            return super()._is_enabled_by_default_on_journal(journal)
        return False

    def _is_compatible_with_journal(self, journal):
        if self.code != "es_verifactu":
            return super()._is_compatible_with_journal(journal)
        return journal.country_code == "ES" and journal.type == "sale"
