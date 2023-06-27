# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo.addons.component.core import Component


class EdiOutputSendL10nEsFacturaeFace(Component):
    _name = "edi.output.send.l10n_es_facturae.l10n_es_facturae_face_cancel_output"
    _usage = "output.send"
    _backend_type = "l10n_es_facturae"
    _exchange_type = "l10n_es_facturae_face_cancel"
    _inherit = ["edi.component.send.mixin", "base.webservice.face"]

    def send(self):
        move = self.exchange_record.record
        parent = self.exchange_record.parent_id
        data = json.loads(self.exchange_record._get_file_content())
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
