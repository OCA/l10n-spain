# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class AccountMoveL10nEsFacturaeFACeListener(Component):
    _name = "account.move.l10n.es.facturae.faceb2b.listener"
    _inherit = "base.event.listener"
    _apply_on = ["account.move"]

    def on_paid_account_move(self, move):
        related_record = move._get_exchange_record(
            self.env.ref(
                "l10n_es_facturae_faceb2b.facturae_faceb2b_exchange_input_type"
            ),
            self.env.ref("l10n_es_facturae_faceb2b.faceb2b_backend"),
        )
        if not related_record or move.l10n_es_facturae_status == "faceb2b-2600":
            return
        client = move.company_id._get_faceb2b_wsdl_client()
        response = client.service.MarkInvoiceAsPaid(
            client.get_type("ns0:MarkInvoiceAsPaidRequestType")(
                registryNumber=related_record.external_identifier,
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
        related_record.l10n_es_facturae_status = "faceb2b-2600"
        move.l10n_es_facturae_status = "faceb2b-2600"

    def on_cancel_account_move(self, move):
        related_record = move._get_exchange_record(
            self.env.ref(
                "l10n_es_facturae_faceb2b.facturae_faceb2b_exchange_input_type"
            ),
            self.env.ref("l10n_es_facturae_faceb2b.faceb2b_backend"),
        )
        if not related_record or move.l10n_es_facturae_status == "faceb2b-2500":
            return
        client = move.company_id._get_faceb2b_wsdl_client()
        response = client.service.RejectInvoice(
            client.get_type("ns0:RejectInvoiceRequestType")(
                registryNumber=related_record.external_identifier,
                reason="R002"
                if move.env.context.get("_facturae_cancel_supplier")
                else "R001",
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
        related_record.l10n_es_facturae_status = "faceb2b-2500"
        move.l10n_es_facturae_status = "faceb2b-2500"

    def on_edi_generate_manual(self, move, exchange_record):
        if exchange_record.type_id.code != "l10n_es_facturae_faceb2b_update":
            return
        exchange_type = self.env.ref(
            "l10n_es_facturae_faceb2b.facturae_faceb2b_exchange_type"
        )
        if move.is_purchase_document():
            exchange_type = self.env.ref(
                "l10n_es_facturae_faceb2b.facturae_faceb2b_exchange_input_type"
            )
        related_record = move._get_exchange_record(
            exchange_type,
            self.env.ref("l10n_es_facturae_faceb2b.faceb2b_backend"),
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
