# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from odoo.exceptions import UserError, ValidationError
from odoo.models import _

from odoo.addons.component.core import Component

from ..models.wsse_signature import MemorySignature

_logger = logging.getLogger(__name__)
try:
    from zeep import Client
except (ImportError, IOError) as err:
    _logger.info(err)


class WebServiceFace(Component):
    _name = "base.webservice.face"
    _usage = "face.protocol"
    _backend_type = "l10n_es_facturae"
    _inherit = "edi.component.mixin"

    def _get_client(self, public_crt, private_key):
        with open(public_crt, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read(), backend=default_backend())
        with open(private_key, "rb") as f:
            key = serialization.load_pem_private_key(
                f.read(), None, backend=default_backend()
            )
        return Client(
            wsdl=self.env["ir.config_parameter"].sudo().get_param("facturae.face.ws"),
            wsse=MemorySignature(
                cert,
                key,
                x509.load_pem_x509_certificate(
                    base64.b64decode(
                        self.env.ref("l10n_es_facturae_face.face_certificate").datas
                    ),
                    backend=default_backend(),
                ),
            ),
        )

    def send_webservice(
        self, public_crt, private_key, file_data, file_name, email, anexos_list=False
    ):
        client = self._get_client(public_crt, private_key)
        invoice_file = client.get_type("ns0:FacturaFile")(
            base64.b64encode(file_data.encode("UTF-8")),
            file_name,
            "application/xml",
        )
        anexos = client.get_type("ns0:ArrayOfAnexoFile")(anexos_list or [])
        invoice_call = client.get_type("ns0:EnviarFacturaRequest")(
            email, invoice_file, anexos
        )
        response = client.service.enviarFactura(invoice_call)
        if response.resultado.codigo != "0":
            raise ValidationError(response.resultado.descripcion)
        return response

    def consult_invoice(self, public_crt, private_key, invoice_number):
        client = self._get_client(public_crt, private_key)
        return client.service.consultarFactura(invoice_number)

    def consult_invoices(self, public_crt, private_key, invoices):
        client = self._get_client(public_crt, private_key)
        request = client.get_type("ns0:ConsultarListadoFacturaRequest")(invoices)
        return client.service.consultarListadoFacturas(request)

    def cancel(self, public_crt, private_key, identifier, motive):
        client = self._get_client(public_crt, private_key)
        response = client.service.anularFactura(identifier, motive)
        if response.resultado.codigo != "0":
            raise UserError(
                _("Connection with FACe returned error %(code)s - %(description)s")
                % {
                    "code": response.resultado.codigo,
                    "description": response.resultado.descripcion,
                }
            )
        return response
