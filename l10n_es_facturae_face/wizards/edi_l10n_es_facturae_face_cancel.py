# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import fields, models


class EdiL10nEsFacturaeFaceCancel(models.TransientModel):
    _name = "edi.l10n.es.facturae.face.cancel"
    _description = "Cancel a FACe Exchange Record"

    move_id = fields.Many2one("account.move", required=True)
    motive = fields.Char(required=True)

    def cancel_face(self):
        self.ensure_one()
        backend = self.env.ref("l10n_es_facturae_face.face_backend")
        exchange_type = self.env.ref("l10n_es_facturae_face.facturae_exchange_type")
        exchange_record = self.move_id._get_exchange_record(exchange_type, backend)
        exchange_record.ensure_one()
        cancel_exchange_record = backend.create_record(
            "l10n_es_facturae_face_cancel",
            {
                "model": self.move_id._name,
                "res_id": self.move_id.id,
                "parent_id": exchange_record.id,
                "edi_exchange_state": "output_pending",
            },
        )
        cancel_exchange_record._set_file_content(json.dumps({"motive": self.motive}))
        backend.with_context(_edi_send_break_on_error=True).exchange_send(
            cancel_exchange_record
        )
        return {}
