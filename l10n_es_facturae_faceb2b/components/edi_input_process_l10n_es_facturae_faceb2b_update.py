# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo.addons.component.core import Component


class EdiInputProcessL10nEsFacturaeFaceUpdate(Component):
    _name = "edi.input.process.l10n_es_facturae.l10n_es_facturae_faceb2b_update"
    _usage = "input.process"
    _backend_type = "l10n_es_facturae"
    _exchange_type = "l10n_es_facturae_faceb2b_update"

    _inherit = "edi.component.input.mixin"

    def process(self):
        data = json.loads(self.exchange_record._get_file_content())
        parent = self.exchange_record.parent_id
        process_code = "faceb2b-" + data["statusInfo"]["status"]["code"]
        revocation_code = False
        if data["cancellationInfo"]["status"]:
            revocation_code = "faceb2b-" + data["cancellationInfo"]["status"]["code"]
        if (
            process_code == parent.l10n_es_facturae_status
            and revocation_code == parent.l10n_es_facturae_cancellation_status
        ):
            return
        parent.write(
            {
                "l10n_es_facturae_status": process_code,
                "l10n_es_facturae_motive": data["statusInfo"]["reason"],
                "l10n_es_facturae_cancellation_status": revocation_code,
                "l10n_es_facturae_cancellation_motive": data["cancellationInfo"][
                    "reason"
                ],
            }
        )
        self.exchange_record.record.write(
            {
                "l10n_es_facturae_status": process_code,
                "l10n_es_facturae_cancellation_status": revocation_code,
            }
        )
