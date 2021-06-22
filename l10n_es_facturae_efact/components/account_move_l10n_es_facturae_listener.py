# Copyright 2021 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class AccountMoveL10nEsFacturaeListener(Component):
    _inherit = "account.move.l10n.es.facturae.listener"

    def _get_exchange_record_vals(self, record):
        res = super()._get_exchange_record_vals(record)
        if record.partner_id.l10n_es_facturae_sending_code == "efact":
            res["exchange_filename"] = "{}@{}@{}".format(
                record.company_id.facturae_efact_code,
                record.partner_id.facturae_efact_code,
                record.name.replace("/", "_"),
            )
        return res
