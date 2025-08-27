# Copyright 2025 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).d

import json

from odoo import models


class L10nEsFacturaeCancelHandler(models.AbstractModel):
    _name = "l10n_es.facturae.face.cancel.handler"
    _description = "Handler to cancel an invoice via FACe webservice"
    _inherit = [
        "edi.oca.handler.output.validate",
        "edi.oca.handler.send",
        "l10n_es.facturae.face.base.handler",
    ]

    def output_validate(self, exchange_record, **kw):
        return True

    def _get_extra_attachment(self, exchange_record):
        return []

    def send(self, exchange_record):
        move = exchange_record.record
        parent = exchange_record.parent_id
        data = json.loads(exchange_record._get_file_content())
        public_crt, private_key = self.env["l10n.es.aeat.certificate"].get_certificates(
            move.company_id
        )
        self.cancel(
            public_crt,
            private_key,
            parent.external_identifier,
            data["motive"],
        )
        cancellation_status = "face-4200"
        parent.l10n_es_facturae_cancellation_status = cancellation_status
        move.l10n_es_facturae_cancellation_status = cancellation_status
        parent.l10n_es_facturae_cancellation_motive = data["motive"]
