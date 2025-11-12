# Copyright 2025 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).d

import json

from odoo import models


class L10nEsFacturaeUpdateHandler(models.AbstractModel):
    _name = "l10n_es.facturae.face.update.handler"
    _description = "Handler to update an invoice via FACe webservice"
    _inherit = [
        "edi.oca.handler.receive",
        "edi.oca.handler.input.validate",
        "edi.oca.handler.process",
        "l10n_es.facturae.face.base.handler",
    ]

    def receive(self, exchange_record):
        invoice = exchange_record.record
        public_crt, private_key = self.env["l10n.es.aeat.certificate"].get_certificates(
            invoice.company_id
        )
        response = self.consult_invoice(
            public_crt,
            private_key,
            exchange_record.parent_id.external_identifier,
        )
        return json.dumps(response)

    def process(self, exchange_record):
        data = json.loads(exchange_record._get_file_content())
        parent = exchange_record.parent_id
        process_code = "face-" + data["statusHistory"][-1]["code"]
        revocation_code = "face-" + data["cancellationRequestStatusCode"]
        if (
            process_code == parent.l10n_es_facturae_status
            and revocation_code == parent.l10n_es_facturae_cancellation_status
        ):
            return
        parent.write(
            {
                "l10n_es_facturae_status": process_code,
                "l10n_es_facturae_motive": data["statusComment"],
                "l10n_es_facturae_cancellation_status": revocation_code,
                "l10n_es_facturae_cancellation_motive": data[
                    "cancellationRequestComment"
                ],
            }
        )
        exchange_record.record.write(
            {
                "l10n_es_facturae_status": process_code,
                "l10n_es_facturae_cancellation_status": revocation_code,
            }
        )

    def input_validate(self, exchange_record, **kw):
        pass
