# Copyright 2025 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).d

from odoo import models


class L10nEsFacturaeOutputHandler(models.AbstractModel):
    _name = "l10n_es.facturae.face.output.handler"
    _description = "Handler to generate and send an invoice via FACe webservice"
    _inherit = [
        "edi.oca.handler.generate",
        "edi.oca.handler.output.validate",
        "edi.oca.handler.send",
        "l10n_es.facturae.face.base.handler",
    ]

    def generate(self, exchange_record):
        report = self.env.ref("l10n_es_facturae.report_facturae_signed")
        report_data = self.env["ir.actions.report"]._render(
            report, exchange_record.record.ids
        )
        return report_data[0]

    def output_validate(self, exchange_record, **kw):
        return True

    def _get_extra_attachment(self, exchange_record):
        return []

    def send(self, exchange_record):
        invoice = exchange_record.record
        public_crt, private_key = self.env["l10n.es.aeat.certificate"].get_certificates(
            invoice.company_id
        )
        response = self.send_webservice(
            public_crt,
            private_key,
            exchange_record._get_file_content(),
            exchange_record.exchange_filename,
            invoice.company_id.face_email,
            self._get_extra_attachment(exchange_record),
        )
        exchange_record.write({"external_identifier": response.factura.numeroRegistro})
