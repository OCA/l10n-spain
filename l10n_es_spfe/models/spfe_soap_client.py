# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
import email
import logging
import uuid
from io import BytesIO

import requests
from lxml import etree

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools import file_open

_logger = logging.getLogger(__name__)

SOAP12_NS = "http://www.w3.org/2003/05/soap-envelope"
SOAP11_NS = "http://schemas.xmlsoap.org/soap/envelope/"
EBMS_NS = "http://docs.oasis-open.org/ebxml-msg/ebms/v3.0/ns/core/200704/"
PARTY_ID_TYPE = "urn:oasis:names:tc:ebcore:partyid-type:iso6523:9920"
_EBMS_XSD_CACHE = {}


class L10nEsSpfeSoap(models.AbstractModel):
    _name = "l10n.es.spfe.soap"
    _description = "AEAT SPFE SOAP 1.2 & ebMS 3.0 Client"

    @api.model
    def _validate_ebms_header(self, messaging_el):
        xsd_path = "l10n_es_spfe/data/xsd-ebms/ebms/ebms-header-3_0-200704.xsd"
        schema = _EBMS_XSD_CACHE.get(xsd_path)
        if schema is None:
            with file_open(xsd_path, "rb") as xsd_stream:
                schema = etree.XMLSchema(etree.parse(xsd_stream))
            _EBMS_XSD_CACHE[xsd_path] = schema
        xml_bytes = etree.tostring(messaging_el, encoding="UTF-8")
        schema.assertValid(etree.parse(BytesIO(xml_bytes)))

    @api.model
    def _build_ebms_soap_envelope(
        self,
        from_party_id,
        to_party_id,
        service,
        action,
        attachments=None,
        message_properties=None,
        message_id=None,
        conversation_id=None,
    ):
        """Construct SOAP 1.2 envelope with ebMS 3.0 Messaging header."""
        nsmap = {"soap": SOAP12_NS, "eb": EBMS_NS}
        env_el = etree.Element(f"{{{SOAP12_NS}}}Envelope", nsmap=nsmap)
        header_el = etree.SubElement(env_el, f"{{{SOAP12_NS}}}Header")
        messaging_el = etree.SubElement(header_el, f"{{{EBMS_NS}}}Messaging")
        user_msg = etree.SubElement(messaging_el, f"{{{EBMS_NS}}}UserMessage")

        msg_info = etree.SubElement(user_msg, f"{{{EBMS_NS}}}MessageInfo")
        now_utc = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )
        etree.SubElement(msg_info, f"{{{EBMS_NS}}}Timestamp").text = now_utc
        msg_id = message_id or f"{uuid.uuid4()}@spfe.odoo"
        etree.SubElement(msg_info, f"{{{EBMS_NS}}}MessageId").text = msg_id

        party_info = etree.SubElement(user_msg, f"{{{EBMS_NS}}}PartyInfo")
        from_el = etree.SubElement(party_info, f"{{{EBMS_NS}}}From")
        etree.SubElement(
            from_el, f"{{{EBMS_NS}}}PartyId", type=PARTY_ID_TYPE
        ).text = from_party_id
        etree.SubElement(from_el, f"{{{EBMS_NS}}}Role").text = "ebms:initiator"
        to_el = etree.SubElement(party_info, f"{{{EBMS_NS}}}To")
        etree.SubElement(
            to_el, f"{{{EBMS_NS}}}PartyId", type=PARTY_ID_TYPE
        ).text = to_party_id
        etree.SubElement(to_el, f"{{{EBMS_NS}}}Role").text = "ebms:responder"

        collab = etree.SubElement(user_msg, f"{{{EBMS_NS}}}CollaborationInfo")
        etree.SubElement(collab, f"{{{EBMS_NS}}}Service").text = service
        etree.SubElement(collab, f"{{{EBMS_NS}}}Action").text = action
        etree.SubElement(collab, f"{{{EBMS_NS}}}ConversationId").text = (
            conversation_id or str(uuid.uuid4())
        )

        if message_properties:
            props_el = etree.SubElement(user_msg, f"{{{EBMS_NS}}}MessageProperties")
            for prop_name, prop_val in message_properties:
                etree.SubElement(
                    props_el, f"{{{EBMS_NS}}}Property", name=prop_name
                ).text = str(prop_val)

        if attachments:
            payload_el = etree.SubElement(user_msg, f"{{{EBMS_NS}}}PayloadInfo")
            for cid, _xml_payload in attachments:
                part_info = etree.SubElement(
                    payload_el, f"{{{EBMS_NS}}}PartInfo", href=f"cid:{cid}"
                )
                part_props = etree.SubElement(part_info, f"{{{EBMS_NS}}}PartProperties")
                etree.SubElement(
                    part_props, f"{{{EBMS_NS}}}Property", name="MimeType"
                ).text = "application/xml"

        etree.SubElement(env_el, f"{{{SOAP12_NS}}}Body")
        self._validate_ebms_header(messaging_el)
        soap_bytes = etree.tostring(
            env_el, xml_declaration=True, encoding="UTF-8", pretty_print=True
        )
        return soap_bytes, msg_id

    @api.model
    def _build_multipart_related_body(self, soap_bytes, soap_action, attachments):
        """Encode SOAP 1.2 + UBL attachments as RFC 2387 multipart/related."""
        boundary = f"====spfe_{uuid.uuid4().hex}===="
        root_cid = f"rootpart_{uuid.uuid4().hex}@spfe.odoo"
        chunks = [
            f"--{boundary}\r\n".encode(),
            (
                f"Content-Type: application/soap+xml; charset=UTF-8; "
                f'action="{soap_action}"\r\n'
                f"Content-Transfer-Encoding: 8bit\r\n"
                f"Content-ID: <{root_cid}>\r\n\r\n"
            ).encode(),
            soap_bytes,
            b"\r\n",
        ]
        for cid, payload_bytes in attachments:
            chunks.extend(
                [
                    f"--{boundary}\r\n".encode(),
                    (
                        f"Content-Type: application/xml; charset=UTF-8\r\n"
                        f"Content-Transfer-Encoding: 8bit\r\n"
                        f"Content-ID: <{cid}>\r\n\r\n"
                    ).encode(),
                    payload_bytes,
                    b"\r\n",
                ]
            )
        chunks.append(f"--{boundary}--\r\n".encode())
        content_type = (
            f'multipart/related; type="application/soap+xml"; '
            f'start="<{root_cid}>"; boundary="{boundary}"; '
            f'action="{soap_action}"'
        )
        return b"".join(chunks), content_type

    @api.model
    def _post_spfe_http(self, company, url, headers, body_bytes):
        """Execute mutual-TLS HTTPS POST to AEAT SPFE using l10n_es_aeat certificate."""
        public_crt, private_key = self.env["l10n.es.aeat.certificate"].get_certificates(
            company=company
        )
        if not public_crt or not private_key:
            raise UserError(
                self.env._(
                    "Please configure an active AEAT X.509 certificate for "
                    "company '%(company)s'.",
                    company=company.display_name,
                )
            )
        try:
            with requests.Session() as session:
                session.cert = (public_crt, private_key)
                resp = session.post(url, data=body_bytes, headers=headers, timeout=60)
        except requests.RequestException as err:
            raise UserError(
                self.env._(
                    "Connection error communicating with AEAT SPFE (%(url)s): "
                    "%(error)s",
                    url=url,
                    error=str(err),
                )
            ) from err
        return resp.status_code, dict(resp.headers), resp.content

    @api.model
    def _parse_spfe_http_response(self, status_code, headers, raw_body):
        """Parse multipart/related or application/soap+xml response & SOAP Faults."""
        ctype = headers.get("Content-Type") or headers.get("content-type") or ""
        soap_xml = None
        attachments = {}

        if "multipart/" in ctype.lower():
            raw_mime = (
                f"Content-Type: {ctype}\r\nMIME-Version: 1.0\r\n\r\n".encode()
                + raw_body
            )
            msg = email.message_from_bytes(raw_mime)
            for idx, part in enumerate(msg.walk()):
                if part.is_multipart():
                    continue
                payload = part.get_payload(decode=True) or part.as_bytes()
                part_ct = (part.get_content_type() or "").lower()
                cid = (part.get("Content-ID") or f"part_{idx}").strip("<>")
                if soap_xml is None and (
                    "soap+xml" in part_ct or b"Envelope" in payload[:300]
                ):
                    soap_xml = payload
                else:
                    attachments[cid] = payload
        else:
            soap_xml = raw_body

        if soap_xml:
            self._check_soap_fault(soap_xml, status_code)

        if status_code >= 400 and not attachments:
            raise UserError(
                self.env._(
                    "AEAT SPFE returned HTTP %(code)s: %(body)s",
                    code=status_code,
                    body=raw_body[:500].decode("utf-8", errors="replace"),
                )
            )
        return {
            "status_code": status_code,
            "soap_xml": soap_xml,
            "attachments": attachments,
        }

    @api.model
    def _check_soap_fault(self, soap_xml, status_code):
        try:
            root = etree.fromstring(soap_xml)
        except etree.XMLSyntaxError:
            return
        faults = root.xpath("//*[local-name()='Fault']")
        if not faults:
            return
        fault = faults[0]
        code_nodes = fault.xpath(
            ".//*[local-name()='Value' or local-name()='faultcode']"
        )
        reason_nodes = fault.xpath(
            ".//*[local-name()='Text' or local-name()='faultstring']"
        )
        fcode = (
            code_nodes[0].text.strip()
            if (code_nodes and code_nodes[0].text)
            else str(status_code)
        )
        freason = (
            reason_nodes[0].text.strip()
            if (reason_nodes and reason_nodes[0].text)
            else "SOAP Fault"
        )
        raise UserError(
            self.env._(
                "AEAT SPFE SOAP Fault (%(code)s): %(reason)s",
                code=fcode,
                reason=freason,
            )
        )

    @api.model
    def call_ebms_service(
        self,
        company,
        service_key,
        attachments=None,
        message_properties=None,
    ):
        """Invoke any SPFE ebMS 3.0 SOAP 1.2 endpoint and return parsed payload."""
        agency = company._get_spfe_tax_agency()
        conn = agency._get_spfe_connection_info(company, service_key)
        from_party = company._get_spfe_sender_party_id()
        if not from_party:
            raise UserError(
                self.env._(
                    "Company '%(company)s' is missing a NIF for SPFE.",
                    company=company.display_name,
                )
            )
        attachments = attachments or []
        soap_bytes, msg_id = self._build_ebms_soap_envelope(
            from_party_id=from_party,
            to_party_id=conn["to_party_id"],
            service=conn["eb_service"],
            action=conn["eb_action"],
            attachments=attachments,
            message_properties=message_properties,
        )
        if attachments:
            body_bytes, content_type = self._build_multipart_related_body(
                soap_bytes, conn["soap_action"], attachments
            )
        else:
            body_bytes = soap_bytes
            content_type = (
                f'application/soap+xml; charset=UTF-8; action="{conn["soap_action"]}"'
            )

        status_code, resp_headers, raw_resp = self._post_spfe_http(
            company,
            conn["url"],
            {"Content-Type": content_type},
            body_bytes,
        )
        parsed = self._parse_spfe_http_response(status_code, resp_headers, raw_resp)
        parsed["message_id"] = msg_id
        parsed["request_soap_xml"] = soap_bytes
        return parsed

    @api.model
    def validate_invoice_pre(self, company, invoice_xml_bytes):
        """Invoke ValidationInvoiceSOAP (direct SOAP 1.2 body, PRE only)."""
        agency = company._get_spfe_tax_agency()
        conn = agency._get_spfe_connection_info(company, "validate_pre")
        inv_el = etree.fromstring(invoice_xml_bytes)

        env_el = etree.Element(f"{{{SOAP12_NS}}}Envelope", nsmap={"soap": SOAP12_NS})
        etree.SubElement(env_el, f"{{{SOAP12_NS}}}Header")
        body_el = etree.SubElement(env_el, f"{{{SOAP12_NS}}}Body")
        body_el.append(inv_el)
        soap_bytes = etree.tostring(
            env_el, xml_declaration=True, encoding="UTF-8", pretty_print=True
        )
        content_type = (
            f'application/soap+xml; charset=UTF-8; action="{conn["soap_action"]}"'
        )
        status_code, resp_headers, raw_resp = self._post_spfe_http(
            company,
            conn["url"],
            {"Content-Type": content_type},
            soap_bytes,
        )
        parsed = self._parse_spfe_http_response(status_code, resp_headers, raw_resp)
        root = etree.fromstring(parsed["soap_xml"])
        ds_nodes = root.xpath("//*[local-name()='DocumentStatus']")
        if not ds_nodes:
            raise UserError(
                self.env._(
                    "Unexpected ValidationInvoiceSOAP response without DocumentStatus."
                )
            )
        ds_bytes = etree.tostring(ds_nodes[0], encoding="UTF-8")
        return {
            "request_soap_xml": soap_bytes,
            "response_xml": ds_bytes,
            "status_dict": self.env["base.ubl"].spfe_parse_document_status_xml(
                ds_bytes
            ),
        }
