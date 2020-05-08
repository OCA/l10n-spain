# -*- coding: utf-8 -*-
# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime
from ..ticketbai.xml_schema import XMLSchema, TicketBaiInvoiceTypeEnum
from .ticketbai_invoice import TicketBaiQRParams, TicketBaiIdentifierValuesIndex
from odoo import models, fields


class TicketBaiInvoiceCustomerInvoice(models.Model):
    _name = 'tbai.invoice.customer.invoice'
    _inherit = 'tbai.invoice'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Related Invoice', required=True, ondelete='restrict')
    partner_id = fields.Many2one(comodel_name='res.partner', related='invoice_id.partner_id', readonly=True, store=True)

    def __init__(self, pool, cr):
        super(TicketBaiInvoiceCustomerInvoice, self).__init__(pool, cr)
        type(self).TicketBAIXMLSchema = XMLSchema(TicketBaiInvoiceTypeEnum.customer_invoice)

    def _get_tbai_identifier_values(self):
        self.ensure_one()
        res = super()._get_tbai_identifier_values()
        invoice_date = self.invoice_id.tbai_get_value_FechaExpedicionFactura()
        res[TicketBaiIdentifierValuesIndex.invoice_date.value] = \
            datetime.strptime(invoice_date, "%d-%m-%Y").strftime("%d%m%y")
        return res

    def _get_qr_url_values(self):
        self.ensure_one()
        res = super()._get_qr_url_values()
        res[TicketBaiQRParams.invoice_number_prefix.value] = self.invoice_id.tbai_get_value_SerieFactura()
        res[TicketBaiQRParams.invoice_number.value] = self.invoice_id.tbai_get_value_NumFactura()
        res[TicketBaiQRParams.invoice_total_amount.value] = self.invoice_id.tbai_get_value_ImporteTotalFactura()
        return res

    def tbai_get_context_records_Sujetos(self):
        return self.invoice_id

    def tbai_get_context_records_Factura(self):
        return self.invoice_id

    def tbai_get_context_records_HuellaTBAI(self):
        return self.invoice_id
