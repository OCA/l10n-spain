# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class EdiWebServiceReceiveFaceL10nEsFacturaeFaceUpdate(Component):
    _name = "edi.input.process.face.l10n_es_facturae_faceb2b_update"
    _usage = "input.process"
    _backend_type = "l10n_es_facturae"
    _exchange_type = "l10n_es_facturae_faceb2b_input"
    _inherit = ["edi.component.receive.mixin", "base.webservice.face"]

    def _get_wsdl(self):
        return self.env["ir.config_parameter"].sudo().get_param("facturae.faceb2b.ws")

    def process(self):
        journal = self.exchange_record.record
        attachment = self.env["ir.attachment"].create(
            {
                "name": self.exchange_record.exchange_filename,
                "datas": self.exchange_record.exchange_file,
            }
        )
        move = journal.with_context(
            default_journal_id=journal.id, default_move_type="in_invoice"
        )._create_invoice_from_attachment(attachment.ids)
        self.exchange_record.write(
            {
                "model": move._name,
                "res_id": move.id,
            }
        )
        public_crt, private_key = self.env["l10n.es.aeat.certificate"].get_certificates(
            journal.company_id
        )
        client = self._get_client(public_crt, private_key)
        result = client.service.ConfirmInvoiceDownload(
            client.get_type("ns0:ConfirmInvoiceDownloadRequestType")(
                registryNumber=self.exchange_record.external_identifier
            )
        )
        if result.code != "0":
            raise UserError(_("Invoice cannot be marked as downloaded"))
