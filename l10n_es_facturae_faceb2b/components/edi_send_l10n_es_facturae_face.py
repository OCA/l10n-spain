# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component


class EdiOutputSendL10nEsFacturaeFace(Component):
    _name = "edi.output.send.l10n_es_facturae.l10n_es_facturae_faceb2b_output"
    _usage = "output.send"
    _backend_type = "l10n_es_facturae"
    _exchange_type = "l10n_es_facturae_faceb2b"
    _inherit = ["edi.output.send.l10n_es_facturae.l10n_es_facturae_face_output"]

    def _get_wsdl(self):
        return self.env["ir.config_parameter"].sudo().get_param("facturae.faceb2b.ws")

    def _get_external_identifier(self, response):
        return response.invoiceDetail.registryNumber

    def send_webservice(
        self, public_crt, private_key, file_data, file_name, email, anexos_list=False
    ):
        client = self._get_client(public_crt, private_key)
        invoice_file = client.get_type("ns0:InvoiceFileType")(
            file_data.encode("UTF-8"),
            file_name,
            "text/xml",
        )
        invoice_call = client.get_type("ns0:SendInvoiceRequestType")(invoice_file)
        response = client.service.SendInvoice(invoice_call)
        if response.resultStatus.code != "0":
            raise ValidationError(
                _("%s - %s - %s")
                % (
                    response.resultStatus.code,
                    response.resultStatus.message,
                    response.resultStatus.detail,
                )
            )
        return response
