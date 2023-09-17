# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    import_faceb2b = fields.Boolean()
    facturae_faceb2b_dire = fields.Char()

    def _cron_facturae_faceb2b(self):
        for journal in self.search(
            [("import_faceb2b", "=", True), ("type", "=", "purchase")]
        ):
            client = journal.company_id._get_faceb2b_wsdl_client()
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

    def _cron_facturae_cancel_faceb2b(self):
        for journal in self.search(
            [("import_faceb2b", "=", True), ("type", "=", "purchase")]
        ):
            client = journal.company_id._get_faceb2b_wsdl_client()
            journal.with_company(
                journal.company_id.id
            )._cancel_facturae_faceb2b_records(client)

    def _cancel_facturae_faceb2b_records(self, client):
        cancel_invoices = client.service.GetInvoiceCancellations(
            client.get_type("ns0:GetInvoiceCancellationsRequestType")(
                receivingUnit=self.facturae_faceb2b_dire
            )
        )
        if cancel_invoices.resultStatus.code != "0":
            _logger.warning(
                "Something happened and we had a problem "
                "receiving the request to cancel invoices: %s - %s - %s"
                % (
                    cancel_invoices.resultStatus.code,
                    cancel_invoices.resultStatus.message,
                    cancel_invoices.resultStatus.detail,
                )
            )
            return
        if not cancel_invoices.invoiceCancellationRequests:
            _logger.debug("No requests to cancel invoices for %s" % self.display_name)
            return
        _logger.debug(
            "%s new requests to cancel invoice detected for %s"
            % (len(cancel_invoices.invoiceCancellationRequests), self.display_name)
        )
        backend = self.env.ref("l10n_es_facturae_faceb2b.faceb2b_backend")
        input_type = self.env.ref(
            "l10n_es_facturae_faceb2b.facturae_faceb2b_exchange_cancel_input_type"
        )
        parent_type = self.env.ref(
            "l10n_es_facturae_faceb2b.facturae_faceb2b_exchange_input_type"
        )
        for (
            registry_number
        ) in cancel_invoices.invoiceCancellationRequests.registryNumber:
            parent = self.env["edi.exchange.record"].search(
                [
                    ("type_id", "=", parent_type.id),
                    ("backend_id", "=", backend.id),
                    ("external_identifier", "=", registry_number),
                ],
                limit=1,
            )
            if not parent:
                continue
            backend.create_record(
                input_type.code,
                {
                    "parent_id": parent.id,
                    "external_identifier": registry_number,
                    "edi_exchange_state": "input_pending",
                    "model": parent.model,
                    "res_id": parent.res_id,
                },
            )
