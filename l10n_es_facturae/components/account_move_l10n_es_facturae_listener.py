# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class AccountMoveL10nEsFacturaeListener(Component):
    _name = "account.move.l10n.es.facturae.listener"
    _inherit = "base.event.listener"
    _apply_on = ["account.move"]

    def _get_backend(self, record):
        return record._get_l10n_es_facturae_backend()

    def _get_exchange_record_vals(self, record):
        return {
            "model": record._name,
            "res_id": record.id,
        }

    def on_post_account_move(self, records):
        for record in records:
            if record.disable_edi_auto:
                continue
            partner = record.partner_id
            if record.move_type not in ["out_invoice", "out_refund"]:
                continue
            if not partner.facturae or not partner.l10n_es_facturae_sending_code:
                continue
            backend = self._get_backend(record)
            if not backend:
                continue
            exchange_type = "l10n_es_facturae"
            if record._has_exchange_record(exchange_type, backend):
                continue
            exchange_record = backend.create_record(
                exchange_type, self._get_exchange_record_vals(record)
            )
            backend._delay_action(exchange_record).exchange_generate(exchange_record)

    def on_generate_account_edi(self, records):
        return self.on_post_account_move(records)
