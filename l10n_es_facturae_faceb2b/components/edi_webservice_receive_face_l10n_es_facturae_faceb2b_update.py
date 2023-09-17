# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from zeep import helpers

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class EdiWebServiceReceiveFaceL10nEsFacturaeFaceUpdate(Component):
    _name = "edi.webservice.receive.face.l10n_es_facturae_faceb2b_update"
    _usage = "input.receive.faceb2b"
    _backend_type = "l10n_es_facturae"
    _exchange_type = None
    _inherit = ["edi.component.receive.mixin", "base.webservice.face"]

    def _get_wsdl(self):
        return self.env["ir.config_parameter"].sudo().get_param("facturae.faceb2b.ws")

    def consult_invoice(self, public_crt, private_key, invoice_number):
        client = self._get_client(public_crt, private_key)
        return client.service.GetInvoiceDetails(
            client.get_type("ns0:GetInvoiceDetailsRequestType")(invoice_number)
        )

    def receive(self):
        invoice = self.exchange_record.record
        public_crt, private_key = self.env["l10n.es.aeat.certificate"].get_certificates(
            invoice.company_id
        )
        response = self.consult_invoice(
            public_crt,
            private_key,
            self.exchange_record.parent_id.external_identifier,
        )
        if response.resultStatus.code != "0":
            raise UserError(
                _("Connection with FACe returned error %s - %s - %s")
                % (
                    response.resultStatus.code,
                    response.resultStatus.message,
                    response.resultStatus.detail,
                )
            )
        return json.dumps(helpers.serialize_object(response.invoiceDetail), default=str)
