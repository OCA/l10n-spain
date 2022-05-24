# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging

from zeep import helpers

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class EdiExchangeRecord(models.Model):
    _inherit = "edi.exchange.record"

    l10n_es_facturae_status = fields.Selection(
        selection=lambda r: r.env["account.move"]
        ._fields["l10n_es_facturae_status"]
        .selection,
        readonly=True,
        string="Facturae State",
    )
    l10n_es_facturae_cancellation_status = fields.Selection(
        selection=lambda r: r.env["account.move"]
        ._fields["l10n_es_facturae_cancellation_status"]
        .selection,
        readonly=True,
        string="Facturae Cancellation state",
    )
    l10n_es_facturae_motive = fields.Text(
        string="Facturae description",
        readonly=True,
    )
    l10n_es_facturae_cancellation_motive = fields.Text(
        readonly=True, string="Facturae Cancellation motive"
    )

    def _cron_face_update_method(self, company_domain=False):
        if not company_domain:
            company_domain = []
        face = self.env.ref("l10n_es_facturae_face.face_backend")
        integrations = self.search(
            [
                ("backend_id", "=", face.id),
                (
                    "edi_exchange_state",
                    "in",
                    ["output_sent_and_processed", "output_sent"],
                ),
                ("model", "=", "account.move"),
                "|",
                ("l10n_es_facturae_status", "=", False),
                (
                    "l10n_es_facturae_status",
                    "in",
                    ["face-1200", "face-1300", "face-2400"],
                ),
            ]
        )
        if not integrations:
            return
        for company in self.env["res.company"].search(company_domain):
            company_integrations = integrations.filtered(
                lambda r: r.record.company_id == company
            )
            if not company_integrations:
                continue
            exchange_dict = {}
            exchanges = []
            for integration in company_integrations:
                exchanges.append(integration.external_identifier)
                exchange_dict[integration.external_identifier] = integration
            public_crt, private_key = self.env[
                "l10n.es.aeat.certificate"
            ].get_certificates(company)
            response = face._find_component(
                face._name,
                ["face.protocol"],
                work_ctx={"exchange_record": self.env["edi.exchange.record"]},
            ).consult_invoices(
                public_crt,
                private_key,
                exchanges,
            )
            if response.resultado.codigo != "0":
                _logger.info(_("Company %s cannot be processed") % company.display_name)
                continue
            for invoice in response.facturas.consultarListadoFactura:
                exchange_record = exchange_dict[invoice.factura.numeroRegistro]
                if invoice.codigo != "0":
                    # Probably processed from another system
                    continue
                process_code = "face-" + invoice.factura.tramitacion.codigo
                revocation_code = "face-" + invoice.factura.anulacion.codigo
                if (
                    exchange_record.l10n_es_facturae_status == process_code
                    and exchange_record.l10n_es_facturae_cancellation_status
                    == revocation_code
                ):
                    continue
                update_record = face.create_record(
                    "l10n_es_facturae_face_update",
                    {
                        "edi_exchange_state": "input_received",
                        "model": exchange_record.model,
                        "res_id": exchange_record.res_id,
                        "parent_id": exchange_record.id,
                    },
                )
                update_record._set_file_content(
                    json.dumps(helpers.serialize_object(invoice.factura))
                )
                face.with_context(_edi_send_break_on_error=True).exchange_process(
                    update_record
                )
