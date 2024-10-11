# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class EdiWebServiceReceiveFaceL10nEsFacturaeFaceUpdate(Component):
    _name = "edi.webservice.receive.face.l10n_es_facturae_faceb2b"
    _usage = "input.receive"
    _backend_type = "l10n_es_facturae"
    _exchange_type = "l10n_es_facturae_faceb2b_input"
    _inherit = "edi.component.receive.mixin"

    def receive(self):
        journal = self.exchange_record.record
        client = journal.company_id._get_faceb2b_wsdl_client()
        result = client.service.DownloadInvoice(
            client.get_type("ns0:DownloadInvoiceRequestType")(
                registryNumber=self.exchange_record.external_identifier
            )
        )
        if result.resultStatus.code != "0":
            raise UserError(_("Invoice cannot be downloaded"))
        # TODO: What should we do with the attachment if it exists?
        return result.invoiceFile.content
