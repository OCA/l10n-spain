# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime
from collections import OrderedDict
from ..ticketbai.xml_schema import XMLSchema, TicketBaiInvoiceTypeEnum
from .ticketbai_invoice import TicketBaiQRParams, TicketBaiIdentifierValuesIndex
from odoo import models, fields, _, api


class TicketBaiInvoiceCustomerInvoice(models.Model):
    _name = 'tbai.invoice.customer.invoice'
    _inherit = 'tbai.invoice'

    @api.multi
    def send(self, **kwargs):
        self.ensure_one()
        return super().send(invoice_id=self.invoice_id.id, **kwargs)

    @api.multi
    def recreate(self):
        self.mapped('invoice_id').tbai_rebuild_customer_invoice()

    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Related Invoice', required=True,
        ondelete='restrict')
    partner_id = fields.Many2one(
        comodel_name='res.partner', related='invoice_id.partner_id', readonly=True,
        store=True)

    def __init__(self, pool, cr):
        super(TicketBaiInvoiceCustomerInvoice, self).__init__(pool, cr)
        type(self).TicketBAIXMLSchema = XMLSchema(
            TicketBaiInvoiceTypeEnum.customer_invoice)

    def _get_tbai_identifier_values(self):
        self.ensure_one()
        res = super()._get_tbai_identifier_values()
        invoice_date = self.invoice_id.tbai_get_value_fecha_expedicion_factura()
        res[TicketBaiIdentifierValuesIndex.invoice_date.value] = \
            datetime.strptime(invoice_date, "%d-%m-%Y").strftime("%d%m%y")
        return res

    def _get_qr_url_values(self):
        self.ensure_one()
        res = super()._get_qr_url_values()
        res[TicketBaiQRParams.invoice_number_prefix.value] = \
            self.invoice_id.tbai_get_value_serie_factura()
        res[TicketBaiQRParams.invoice_number.value] = \
            self.invoice_id.tbai_get_value_num_factura()
        res[TicketBaiQRParams.invoice_total_amount.value] = \
            self.invoice_id.tbai_get_value_importe_total_factura()
        return res

    def tbai_build_sujetos(self):
        return OrderedDict([
            ("Emisor", self.invoice_id.tbai_build_emisor()),
            ("Destinatarios", self.invoice_id.tbai_build_destinatarios())
        ])

    def tbai_build_factura(self):
        return OrderedDict([
            ("CabeceraFactura", self.invoice_id.tbai_build_cabecera_factura()),
            ("DatosFactura", self.invoice_id.tbai_build_datos_factura()),
            ("TipoDesglose", self.invoice_id.tbai_build_tipo_desglose()),
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
