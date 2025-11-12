# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo.addons.component.core import Component


class EdiWebServiceReceiveFaceL10nEsFacturaeFaceUpdate(Component):
    _name = "edi.webservice.receive.face.l10n_es_facturae_face_update"
    _usage = "input.receive"
    _backend_type = "l10n_es_facturae"
    _exchange_type = "l10n_es_facturae_face_update"
    _inherit = ["edi.component.receive.mixin", "base.webservice.face"]

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
        return json.dumps(response)
