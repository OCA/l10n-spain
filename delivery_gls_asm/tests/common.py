# Copyright 2026 PYMING - Extreme Micro S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import smtplib
import socket
import urllib.request
from unittest.mock import Mock, patch

import requests
from suds.sax.parser import Parser
from suds.transport.http import HttpTransport
from suds.umx.basic import Basic

from ..models import gls_asm_request

LABEL_PDF = b"%PDF-1.4\nSynthetic GLS label\n%%EOF"
NOT_FOUND = (
    "<response><expediciones><Error>No se encuentra la expedición</Error>"
    "</expediciones></response>"
)


def soap_response(xml):
    """Unmarshal synthetic XML exactly as suds does, without any transport."""
    return Basic().process(Parser().parse(string=xml).root())


class GlsAsmOfflineMixin:
    """Keep real request builders/conversion; prohibit network and filestore writes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))
        cls.network_guards = []
        for target, method in (
            (socket.socket, "connect"),
            (socket.socket, "connect_ex"),
            (socket, "create_connection"),
            (requests.Session, "request"),
            (urllib.request.OpenerDirector, "open"),
            (HttpTransport, "open"),
            (HttpTransport, "send"),
            (smtplib.SMTP, "connect"),
        ):
            cls.network_guards.append(
                cls.startClassPatcher(
                    patch.object(
                        target,
                        method,
                        side_effect=AssertionError("Unexpected external transport"),
                    )
                )
            )
        cls.client = cls.startClassPatcher(
            patch.object(
                gls_asm_request,
                "Client",
                side_effect=AssertionError("Unexpected SOAP client initialization"),
            )
        )
        cls.startClassPatcher(
            patch.object(
                cls.env.registry["delivery.carrier"],
                "_gls_asm_uid",
                return_value="SYNTHETIC",
            )
        )
        # Native DB attachment storage rolls back together with the test cursor.
        cls.startClassPatcher(
            patch.object(
                cls.env.registry["ir.attachment"], "_storage", return_value="db"
            )
        )
        cls.env.company.stock_move_email_validation = False

    def setUp(self):
        super().setUp()
        # Do not clear transport calls: attempts during class fixtures must also fail.
        self.client.reset_mock()
        self.client.side_effect = AssertionError(
            "Unexpected SOAP client initialization"
        )
        self.soap_service = Mock(
            spec_set=[
                "GrabaServicios",
                "GetExpCli",
                "Anula",
                "EtiquetaEnvio",
                "Tracking",
            ]
        )
        for method in self.soap_service._mock_methods:
            getattr(self.soap_service, method).side_effect = AssertionError(
                f"Unexpected SOAP operation: {method}"
            )
        self.client.return_value = Mock(service=self.soap_service)
        self.allowed_soap_calls = {}

    def tearDown(self):
        # Product code may catch transport exceptions: still fail the test loudly.
        try:
            for guard in self.network_guards:
                guard.assert_not_called()
            if not self.allowed_soap_calls:
                self.client.assert_not_called()
            for method in self.soap_service._mock_methods:
                self.assertEqual(
                    getattr(self.soap_service, method).call_count,
                    self.allowed_soap_calls.get(method, 0),
                    f"Unexpected or missing SOAP operation: {method}",
                )
        finally:
            super().tearDown()

    def _allow_soap(self, **responses):
        """Allow only explicitly queued operations on the mocked client."""
        self.client.side_effect = None
        for method, xml_responses in responses.items():
            self.allowed_soap_calls[method] = len(xml_responses)
            getattr(self.soap_service, method).side_effect = [
                soap_response(xml) for xml in xml_responses
            ]

    def _booking_response(self, reference, barcode, picking_ref, label):
        return f"""<response><Servicios>
            <Envio codexp="{reference}" codbarras="{barcode}">
                <Resultado return="0" />
                <Referencias>
                    <Referencia tipo="N">{picking_ref}</Referencia>
                    <Referencia tipo="C">SYNTHETIC</Referencia>
                </Referencias>
                <Etiquetas><Etiqueta tipo="PDF">{label}</Etiqueta></Etiquetas>
            </Envio>
        </Servicios></response>"""
