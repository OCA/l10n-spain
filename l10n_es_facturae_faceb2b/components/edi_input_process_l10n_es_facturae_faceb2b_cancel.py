# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class EdiInputProcessL10nEsFacturaeFaceCancel(Component):
    _name = "edi.input.process.l10n_es_facturae.l10n_es_facturae_faceb2b_cancel_input"
    _usage = "input.process"
    _backend_type = "l10n_es_facturae"
    _exchange_type = "l10n_es_facturae_faceb2b_cancel_input"

    _inherit = "edi.component.input.mixin"

    def _can_cancel_faceb2b(self):
        move = self.exchange_record.record
        return move.state == "draft"

    def process(self):
        data = json.loads(self.exchange_record._get_file_content())
        client = self.exchange_record.record.company_id._get_faceb2b_wsdl_client()
        parent = self.exchange_record.parent_id
        process_code = self.exchange_record.record.l10n_es_facturae_status
        if self._can_cancel_faceb2b():
            revocation_code = "faceb2b-4300"
            self.exchange_record.record.with_context(
                _facturae_cancel_supplier=True
            ).button_cancel()
            body = (
                _("Cancellation requested and accepted due to:\n %s")
                % data["cancellationInfo"]["requestComment"]
            )
            response = client.service.AcceptInvoiceCancellation(
                client.get_type("ns0:AcceptInvoiceCancellationRequestType")(
                    registryNumber=self.exchange_record.external_identifier
                )
            )
            if response.code != "0":
                raise UserError(_("Invoice cannot be marked as cancellation acepted"))
        else:
            revocation_code = "faceb2b-4400"
            body = (
                _("Cancellation asked but rejected. \nMotive:\n %s")
                % data["cancellationInfo"]["requestComment"]
            )
            response = client.service.RejectInvoiceCancellation(
                client.get_type("ns0:RejectInvoiceCancellationRequestType")(
                    registryNumber=self.exchange_record.external_identifier,
                    comment="Cannot proceed to cancel the invoice",
                )
            )
            if response.code != "0":
                raise UserError(_("Invoice cannot be marked as cancellation rejected"))
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
        self.exchange_record.record.message_post(body=body)
