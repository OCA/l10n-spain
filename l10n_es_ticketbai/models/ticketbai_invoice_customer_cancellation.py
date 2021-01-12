# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import OrderedDict
from ..ticketbai.xml_schema import XMLSchema, TicketBaiInvoiceTypeEnum
from odoo import models, fields, api


class TicketBaiInvoiceCustomerCancellation(models.Model):
    _name = 'tbai.invoice.customer.cancellation'
    _inherit = 'tbai.invoice'

    @api.multi
    def send(self, **kwargs):
        self.ensure_one()
        return super().send(invoice_id=self.invoice_id.id, **kwargs)

    @api.multi
    def recreate(self):
        self.mapped('invoice_id').tbai_rebuild_customer_cancellation()

    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Related Invoice', required=True,
        ondelete='restrict')
    partner_id = fields.Many2one(
        comodel_name='res.partner', related='invoice_id.partner_id', readonly=True,
        store=True)

    def __init__(self, pool, cr):
        super(TicketBaiInvoiceCustomerCancellation, self).__init__(pool, cr)
        type(self).TicketBAIXMLSchema = XMLSchema(
            TicketBaiInvoiceTypeEnum.customer_cancellation)

    def _compute_tbai_identifier(self):
        """Override, not needed for Customer Invoice Cancellation"""
        pass

    def _compute_tbai_qr(self):
        """Override, not needed for Customer Invoice Cancellation"""
        pass

    @api.multi
    @api.depends(
        'company_id', 'company_id.tbai_tax_agency_id',
        'company_id.tbai_tax_agency_id.rest_url_customer_cancellation',
        'company_id.tbai_tax_agency_id.test_rest_url_customer_cancellation'
    )
    def _compute_api_url(self):
        for record in self:
            if record.company_id.tbai_test_enabled:
                url = record.company_id.tbai_tax_agency_id.\
                    test_rest_url_customer_cancellation
            else:
                url = record.company_id.tbai_tax_agency_id.\
                    rest_url_customer_cancellation
            record.api_url = url

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
        res["Software"] = self.company_id.tbai_build_software()
        num_serie_dispositivo = self.company_id.tbai_get_value_num_serie_dispositivo()
        if num_serie_dispositivo:
            res["NumSerieDispositivo"] = num_serie_dispositivo
        return res
