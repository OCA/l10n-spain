# -*- coding: utf-8 -*-
# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import OrderedDict
from ..ticketbai.xml_schema import XMLSchema, TicketBaiInvoiceTypeEnum
from odoo import models, fields, api


class TicketBaiInvoiceCustomerCancellation(models.Model):
    _name = 'tbai.invoice.customer.cancellation'
    _inherit = 'tbai.invoice'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Related Invoice', required=True,
        ondelete='restrict')
    partner_id = fields.Many2one(comodel_name='res.partner',
                                 related='invoice_id.partner_id', readonly=True,
                                 store=True)

    def __init__(self, pool, cr):
        super(TicketBaiInvoiceCustomerCancellation, self).__init__(pool, cr)
        type(self).TicketBAIXMLSchema = XMLSchema(
            TicketBaiInvoiceTypeEnum.customer_cancellation)

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

    def tbai_build_id_factura(self):
        return OrderedDict([
            ("Emisor", self.invoice_id.tbai_build_emisor()),
            ("CabeceraFactura", OrderedDict([
                ("SerieFactura", self.invoice_id.tbai_get_value_serie_factura()),
                ("NumFactura", self.invoice_id.tbai_get_value_num_factura()),
                ("FechaExpedicionFactura",
                    self.invoice_id.tbai_get_value_fecha_expedicion_factura())
            ]))
        ])

    def tbai_build_huella_tbai(self):
        res = OrderedDict({})
        encadenamiento_factura_anterior = \
            self.invoice_id.tbai_build_encadenamiento_factura_anterior()
        if encadenamiento_factura_anterior:
            res["EncadenamientoFacturaAnterior"] = encadenamiento_factura_anterior
        res["Software"] = self.company_id.tbai_build_software()
        num_serie_dispositivo = self.company_id.tbai_get_value_num_serie_dispositivo()
        if num_serie_dispositivo:
            res["NumSerieDispositivo"] = num_serie_dispositivo
        return res
