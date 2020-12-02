# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

from odoo.exceptions import UserError, ValidationError
from odoo.models import _

from odoo.addons.component.core import Component

from ..models.wsse_signature import MemorySignature

_logger = logging.getLogger(__name__)
try:
    from OpenSSL import crypto
    from zeep import Client
except (ImportError, IOError) as err:
    _logger.info(err)


class WebServiceFace(Component):
    _name = "base.webservice.face"
    _usage = "webservice.request"
    _webservice_protocol = "face"
    _inherit = "base.webservice.adapter"

    def _get_client(self, certificate, password):
        cert = crypto.load_pkcs12(base64.b64decode(certificate), password,)
        cert.set_ca_certificates(None)
        return Client(
            wsdl=self.collection.url,
            wsse=MemorySignature(
                cert.export(),
                base64.b64decode(
                    self.env.ref("l10n_es_facturae_face.face_certificate").datas
                ),
            ),
        )

    def send(
        self, certificate, password, file_data, file_name, email, anexos_list=False
    ):
        client = self._get_client(certificate, password)
        invoice_file = client.get_type("ns0:FacturaFile")(
            base64.b64encode(file_data.encode("UTF-8")), file_name, "application/xml",
        )
        anexos = client.get_type("ns0:ArrayOfAnexoFile")(anexos_list or [])
        invoice_call = client.get_type("ns0:EnviarFacturaRequest")(
            email, invoice_file, anexos
        )
        response = client.service.enviarFactura(invoice_call)
        if response.resultado.codigo != "0":
            raise ValidationError(response.resultado.descripcion)
        return response

    def consult_invoice(self, certificate, password, invoice_number):
        client = self._get_client(certificate, password)
        return client.service.consultarFactura(invoice_number)

    def consult_invoices(self, certificate, password, invoices):
        client = self._get_client(certificate, password)
        request = client.get_type("ns0:ConsultarListadoFacturaRequest")(invoices)
        return client.service.consultarListadoFacturas(request)

    def cancel(self, certificate, password, identifier, motive):
        client = self._get_client(certificate, password)
        response = client.service.anularFactura(identifier, motive)
        if response.resultado.codigo != "0":
            raise UserError(
                _("Connection with FACe returned error %s - %s")
                % (response.resultado.codigo, response.resultado.descripcion)
            )
        return response
