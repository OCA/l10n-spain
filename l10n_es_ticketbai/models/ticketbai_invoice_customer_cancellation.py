# -*- coding: utf-8 -*-
# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from ..ticketbai.xml_schema import XMLSchema, TicketBaiInvoiceTypeEnum
from odoo import models, fields, api


class TicketBaiInvoiceCustomerCancellation(models.Model):
    _name = 'tbai.invoice.customer.cancellation'
    _inherit = 'tbai.invoice'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Related Invoice', required=True, ondelete='restrict')
    partner_id = fields.Many2one(comodel_name='res.partner', related='invoice_id.partner_id', readonly=True, store=True)

    def __init__(self, pool, cr):
        super(TicketBaiInvoiceCustomerCancellation, self).__init__(pool, cr)
        type(self).TicketBAIXMLSchema = XMLSchema(TicketBaiInvoiceTypeEnum.customer_cancellation)

    @api.one
    @api.depends('signature_value')
    def _compute_tbai_identifier(self):
        """Override, not needed for Customer Invoice Cancellation"""
        pass

    @api.one
    @api.depends('tbai_identifier')
    def _compute_tbai_qr(self):
        """Override, not needed for Customer Invoice Cancellation"""
        pass

    def tbai_get_context_records_IDFactura(self):
        return self.invoice_id

    def tbai_get_context_records_HuellaTBAI(self):
        return self.invoice_id
