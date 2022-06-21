# Copyright (2021) Binovo IT Human Project SL
# Copyright 2022 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import models

from odoo.addons.l10n_es_ticketbai_api.ticketbai.xml_schema import TicketBaiSchema

_logger = logging.getLogger(__name__)


class TicketBAIInvoice(models.Model):
    _inherit = "tbai.invoice"

    def get_lroe_ticketbai_api(self, **kwargs):
        self.ensure_one()
        cert = self.company_id.tbai_certificate_get_public_key()
        key = self.company_id.tbai_certificate_get_private_key()
        return super().get_lroe_ticketbai_api(cert=cert, key=key, **kwargs)

    def send(self, **kwargs):
        self.ensure_one()
        tbai_tax_agency_id = self.company_id.tbai_tax_agency_id
        if (
            tbai_tax_agency_id
            and tbai_tax_agency_id.id
            == self.env.ref("l10n_es_ticketbai_api_batuz.tbai_tax_agency_bizkaia").id
        ):
            if TicketBaiSchema.TicketBai.value == self.schema and self.invoice_id:
                return self.send_lroe_ticketbai(invoice_id=self.invoice_id.id, **kwargs)
            elif (
                TicketBaiSchema.AnulaTicketBai.value == self.schema
                and self.cancelled_invoice_id
            ):
                return self.send_lroe_ticketbai(
                    invoice_id=self.cancelled_invoice_id.id, **kwargs
                )
            else:
                return self.send_lroe_ticketbai(**kwargs)
        else:
            return super().send(**kwargs)
