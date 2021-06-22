# Copyright 2021 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class AccountMoveL10nEsFacturaeEfactManualListener(Component):
    _name = "account.move.l10n.es.facturae.efact.manual.listener"
    _inherit = "base.event.listener"
    _apply_on = ["account.move"]

    def on_edi_generate_manual(self, move, exchange_record):
        if exchange_record.backend_id != self.env.ref(
            "l10n_es_facturae_efact.efact_backend"
        ):
            return
        exchange_record.exchange_filename = "{}@{}@{}".format(
            move.company_id.facturae_efact_code,
            move.partner_id.facturae_efact_code,
            move.name.replace("/", "_"),
        )
