# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from zeep import Client

from odoo import fields, models

from odoo.addons.l10n_es_facturae_face.models.wsse_signature import MemorySignature

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    import_faceb2b = fields.Boolean()
    facturae_faceb2b_dire = fields.Char()

    def _cron_facturae_faceb2b(self):
        for journal in self.search(
            [("import_faceb2b", "=", True), ("type", "=", "purchase")]
        ):
            public_crt, private_key = self.env[
                "l10n.es.aeat.certificate"
            ].get_certificates(journal.company_id)
            with open(public_crt, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read())
            with open(private_key, "rb") as f:
                key = serialization.load_pem_private_key(f.read(), None)
            client = Client(
                wsdl=self.env["ir.config_parameter"]
                .sudo()
                .get_param("facturae.faceb2b.ws"),
                wsse=MemorySignature(
                    cert,
                    key,
                    x509.load_pem_x509_certificate(
                        base64.b64decode(
                            self.env.ref("l10n_es_facturae_face.face_certificate").datas
                        )
                    ),
                ),
            )
            journal.with_company(
                journal.company_id.id
            )._generate_facturae_faceb2b_records(client)

    def _generate_facturae_faceb2b_records(self, client):
        registered_invoices = client.service.GetRegisteredInvoices(
            client.get_type("ns0:GetRegisteredInvoicesRequestType")(
                receivingUnit=self.facturae_faceb2b_dire
            )
        )
        if registered_invoices.resultStatus.code != "0":
            _logger.warning(
                "Something happened and we had a problem "
                "receiving the registered invoices: %s - %s - %s"
                % (
                    registered_invoices.resultStatus.code,
                    registered_invoices.resultStatus.message,
                    registered_invoices.resultStatus.detail,
                )
            )
            return
        if not registered_invoices.newRegisteredInvoices:
            _logger.debug("No new records for %s" % self.display_name)
            return
        backend = self.env.ref("l10n_es_facturae_faceb2b.faceb2b_backend")
        input_type = self.env.ref(
            "l10n_es_facturae_faceb2b.facturae_faceb2b_exchange_input_type"
        )

        _logger.debug(
            "%s new records detected for %s"
            % (len(registered_invoices.newRegisteredInvoices), self.display_name)
        )
        created = 0
        for (
            registered_invoice
        ) in registered_invoices.newRegisteredInvoices.registryNumber:
            if not self.env["edi.exchange.record"].search(
                [
                    ("type_id", "=", input_type.id),
                    ("backend_id", "=", backend.id),
                    ("external_identifier", "=", registered_invoice),
                ],
                limit=1,
            ):
                backend.create_record(
                    input_type.code,
                    {
                        "external_identifier": registered_invoice,
                        "edi_exchange_state": "input_pending",
                        "model": self._name,
                        "res_id": self.id,
                    },
                )
                created += 1
        _logger.debug("%s new records created for %s" % (created, self.display_name))
