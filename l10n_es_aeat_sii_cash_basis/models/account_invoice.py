# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sii_recc_sent = fields.Boolean(
        string='SII Payment RECC Sent', copy=False, readonly=True)
    sii_recc_csv = fields.Char(
        string='SII Payment RECC CSV', copy=False, readonly=True)
    sii_recc_return = fields.Text(
        string='SII Payment RECC Return', copy=False, readonly=True)
    sii_recc_send_error = fields.Text(string='SII Payment RECC Send Error')

    @api.multi
    def _connect_wsdl(self, wsdl, port_name):
        self.ensure_one()
        company = self.company_id
        client = self._connect_sii(wsdl)
        if company.sii_test:
            port_name += 'Pruebas'
        serv = client.bind('siiService', port_name)
        return serv

    @api.multi
    def send_recc_payment(self, move):
        for invoice in self:
            if invoice.type in ['out_invoice', 'out_refund']:
                wsdl = self.env['ir.config_parameter'].get_param(
                    'l10n_es_aeat_sii.wsdl_pr', False)
                port_name = 'SuministroCobrosEmitidas'
                importe = move.debit
            elif invoice.type in ['in_invoice', 'in_refund']:
                wsdl = self.env['ir.config_parameter'].get_param(
                    'l10n_es_aeat_sii.wsdl_ps', False)
                port_name = 'SuministroPagosRecibidas'
                importe = move.credit
            serv = invoice._connect_wsdl(wsdl, port_name)
            header = invoice._get_sii_header(False)
            fecha = self._change_date_format(move.reconcile_id.create_date)
            pay = {
                'Fecha': fecha,
                'Importe': importe,
                'Medio': invoice.payment_mode_id.sii_key.code,
            }
            try:
                invoice_date = self._change_date_format(invoice.date_invoice)
                if invoice.type in ['out_invoice', 'out_refund']:
                    payment = {
                        "IDFactura": {
                            "IDEmisorFactura": {
                                "NIF": invoice.company_id.vat[2:]
                            },
                            "NumSerieFacturaEmisor": invoice.number[0:60],
                            "FechaExpedicionFacturaEmisor": invoice_date},
                    }
                    payment['Cobros'] = {}
                    payment['Cobros']['Cobro'] = []
                    payment['Cobros']['Cobro'].append(pay)
                    res = serv.SuministroLRCobrosEmitidas(
                        header, payment)
                elif invoice.type in ['in_invoice', 'in_refund']:
                    payment = {
                        "IDFactura": {
                            "IDEmisorFactura": {
                                "NombreRazon": invoice.partner_id.name[0:120]
                            },
                            "NumSerieFacturaEmisor":
                            invoice.supplier_invoice_number and
                            invoice.supplier_invoice_number[0:60],
                            "FechaExpedicionFacturaEmisor": invoice_date},
                    }
                    id_emisor = invoice._get_sii_identifier()
                    payment['IDFactura']['IDEmisorFactura'].update(id_emisor)
                    payment['Pagos'] = {}
                    payment['Pagos']['Pago'] = []
                    payment['Pagos']['Pago'].append(pay)
                    res = serv.SuministroLRPagosRecibidas(
                        header, payment)
                if res['EstadoEnvio'] in ['Correcto', 'AceptadoConErrores']:
                    invoice.sii_recc_sent = True
                    invoice.sii_recc_csv = res['CSV']
                else:
                    invoice.sii_recc_sent = False
                self.sii_recc_return = res
                send_recc_error = False
                res_line = res['RespuestaLinea'][0]
                if res_line['CodigoErrorRegistro']:
                    send_recc_error = u"{} | {}".format(
                        unicode(res_line['CodigoErrorRegistro']),
                        unicode(res_line['DescripcionErrorRegistro'])[:60])
                invoice.sii_send_error = send_recc_error
            except Exception as fault:
                invoice.sii_recc_return = fault
                invoice.sii_send_error = fault
