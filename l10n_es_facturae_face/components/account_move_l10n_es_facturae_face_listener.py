# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class AccountMoveL10nEsFacturaeFACeListener(Component):
    _name = "account.move.l10n.es.facturae.face.listener"
    _inherit = "base.event.listener"
    _apply_on = ["account.move"]

    def on_edi_generate_manual(self, move, exchange_record):
        if exchange_record.type_id.code != "l10n_es_facturae_face_update":
            return
        related_record = move._get_exchange_record(
            self.env.ref("l10n_es_facturae_face.facturae_exchange_type"),
            self.env.ref("l10n_es_facturae_face.face_backend"),
        )
        if not related_record:
            raise UserError(_("Exchange record cannot be found for FACe"))
        if exchange_record.edi_exchange_state == "new":
            exchange_record.write(
                {"edi_exchange_state": "input_pending", "parent_id": related_record.id}
            )
        exchange_record.backend_id.with_context(
            _edi_send_break_on_error=True
        ).exchange_receive(exchange_record)
        exchange_record.backend_id.with_context(
            _edi_send_break_on_error=True
        ).exchange_process(exchange_record)
