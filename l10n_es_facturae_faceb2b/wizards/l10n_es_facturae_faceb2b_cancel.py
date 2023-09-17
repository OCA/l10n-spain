# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class L10nEsFacturaeFaceb2bCancel(models.TransientModel):
    _name = "l10n.es.facturae.faceb2b.cancel"
    _description = "Cancel a FACeB2B Exchange Record"

    move_id = fields.Many2one("account.move", required=True)
    motive = fields.Char(required=True)

    def cancel_faceb2b(self):
        self.ensure_one()
        backend = self.env.ref("l10n_es_facturae_faceb2b.faceb2b_backend")
        exchange_type = self.env.ref(
            "l10n_es_facturae_faceb2b.facturae_faceb2b_exchange_type"
        )
        exchange_record = self.move_id._get_exchange_record(exchange_type, backend)
        exchange_record.ensure_one()
        client = self.move_id.company_id._get_faceb2b_wsdl_client()
        response = client.service.RequestInvoiceCancellation(
            client.get_type("ns0:RequestInvoiceCancellationRequestType")(
                registryNumber=exchange_record.external_identifier,
                reason="C001",
                comment=self.motive,
            )
        )
        if response.code != "0":
            raise UserError(
                _(
                    "Something happened and we had a problem "
                    "receiving the registered invoices: %s - %s - %s"
                    % (
                        response.code,
                        response.message,
                        response.detail,
                    )
                )
            )
        exchange_record.l10n_es_facturae_cancellation_status = "faceb2b-4200"
        self.move_id.l10n_es_facturae_cancellation_status = "faceb2b-4200"
        self.move_id.message_post(
            body=_("Cancellation send to the custmer. Motive:\n%s") % self.motive
        )
