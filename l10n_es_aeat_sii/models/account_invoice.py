# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.osv import osv, fields
from requests import Session
from zeep import Client
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from datetime import datetime


class AccountInvoice(osv.Model):
    _inherit = 'account.invoice'

    _columns = {

        'sii_sent': fields.boolean(string='SII Sent'),
        'sii_return': fields.text(string='SII Return'),
        'refund_type': fields.selection(
            selection=[('S', 'By substitution'), ('I', 'By differences')],
            string="Refund Type")
    }

    def copy(self, cr, uid, id, default, context={}):

        default['sii_sent'] = False
        default['sii_return'] = None

        return super(AccountInvoice, self).copy(cr, uid, id, default, context=context)

    def _change_date_format(self, cr, uid, date):
        datetimeobject = datetime.strptime(date, '%Y-%m-%d')
        new_date = datetimeobject.strftime('%d-%m-%Y')
        return new_date

    def _get_header(self, cr, uid, ids, company, TipoComunicacion):
        header = {
            "IDVersionSii": company.sii_version,
            "Titular": {
                "NombreRazon": company.name,
                "NIF": company.vat[2:]},
            "TipoComunicacion": TipoComunicacion
        }
        return header

    def _get_tax_line_req(self, cr, uid, tax_type, line, line_taxes):
        taxes = False
        if len(line_taxes) > 1:
            req_ids = line_taxes.search([('description', 'in', [
                'P_REQ5.2', 'S_REQ52', 'P_REQ14', 'S_REQ14', 'P_REQ05',
                'S_REQ05'])])
            for tax in line_taxes:
                if tax in req_ids:
                    price = line.price_unit * (1 - (
                        line.discount or 0.0) / 100.0)
                    taxes = tax.compute_all(
                        price, line.quantity, line.product_id,
                        line.invoice_id.partner_id)
                    taxes['percentage'] = tax.amount
                    return taxes
        return taxes


    def _get_sii_tax_line(self, cr, uid, tax_line, line, line_taxes, invoice):
        tax_type = tax_line.amount * 100
        tax_line_req = self._get_tax_line_req(cr, uid, tax_type, line, line_taxes)
        tax = self.pool.get('account.tax').browse(cr, uid, tax_line.id)
        if tax:
           taxes = self.pool.get('account.tax').compute_all(cr, uid, [tax], (line.price_unit * (1 - (line.discount or 0.0) / 100.0)), line.quantity, line.product_id, line.invoice_id.partner_id)
        if tax_line_req:
            TipoRecargo = tax_line_req['percentage'] * 100
            CuotaRecargo = tax_line_req['taxes'][0]['amount']
        else:
            TipoRecargo = 0
            CuotaRecargo = 0
        tax_sii = {
            "TipoImpositivo": tax_type,
            "BaseImponible": taxes['total'],
            "TipoRecargoEquivalencia": TipoRecargo,
            "CuotaRecargoEquivalencia": CuotaRecargo
        }
        if invoice.type in ['out_invoice', 'out_refund']:
            tax_sii['CuotaRepercutida'] = taxes['taxes'][0]['amount']
        if invoice.type in ['in_invoice', 'in_refund']:
            tax_sii['CuotaSoportada'] = taxes['taxes'][0]['amount']
        return tax_sii


    def _update_sii_tax_line(self, cr, uid, taxes, tax_line, line, line_taxes, invoice):
        tax_type = tax_line.amount * 100
        tax_line_req = self._get_tax_line_req(cr, uid, tax_type, line, line_taxes)
        taxes = self.pool.get('account.tax').compute_all(cr, uid, [tax_line.id],
            (line.price_unit * (1 - (line.discount or 0.0) / 100.0)),
            line.quantity, line.product_id, line.invoice_id.partner_id)
        if tax_line_req:
            TipoRecargo = tax_line_req['percentage'] * 100
            CuotaRecargo = tax_line_req['taxes'][0]['amount']
        else:
            TipoRecargoEquivalencia = 0
            CuotaRecargoEquivalencia = 0
        taxes[str(tax_type)]['BaseImponible'] += taxes['total']
        taxes[str(tax_type)]['TipoRecargoEquivalencia'] += TipoRecargo
        taxes[str(tax_type)]['CuotaRecargoEquivalencia'] += CuotaRecargo
        if invoice.type in ['out_invoice', 'out_refund']:
            taxes[str(tax_type)]['CuotaRepercutida'] += taxes['taxes'][0]['amount']
        if invoice.type in ['in_invoice', 'in_refund']:
            taxes[str(tax_type)]['CuotaSoportada'] += taxes['taxes'][0]['amount']
        return taxes

    def _get_sii_out_taxes(self, cr, uid, invoice):
        taxes_sii = {}
        taxes_f = {}
        taxes_to = {}
        for line in invoice.invoice_line:
            for tax_line in line.invoice_line_tax_id:
                if tax_line.description in [
                    'S_IVA21B', 'S_IVA10B', 'S_IVA4B', 'S_IVA0_ISP',
                    'S_IVA_NS']:
                    if 'DesgloseFactura' not in taxes_sii:
                        taxes_sii['DesgloseFactura'] = {}
                    if tax_line.description in [
                        'S_IVA21B', 'S_IVA10B', 'S_IVA4B']:
                        if 'Sujeta' not in taxes_sii['DesgloseFactura']:
                            taxes_sii['DesgloseFactura']['Sujeta'] = {}
                        # TODO l10n_es no tiene impuesto exento de bienes corrientes
                        #                         if tax_line.description in ['S_IVA0']:
                        #                             if 'Exenta' not in taxes_sii['DesgloseFactura'][
                        #                                 'Sujeta']:
                        #                                 taxes_sii['DesgloseFactura']['Sujeta'][
                        #                                     'Exenta'] = {'BaseImponible': line.price_subtotal}
                        #                             else:
                        #                                 taxes_sii['DesgloseFactura']['Sujeta'][
                        #                                     'Exenta']['BaseImponible'] += line.price_subtotal
                        #                         TODO Facturas No sujetas
                        if tax_line.description in [
                            'S_IVA21B', 'S_IVA10B', 'S_IVA4B', 'S_IVA0_ISP']:
                            if 'NoExenta' not in taxes_sii['DesgloseFactura'][
                                'Sujeta']:
                                taxes_sii['DesgloseFactura']['Sujeta'][
                                    'NoExenta'] = {}
                            if tax_line.description in ['S_IVA0_ISP']:
                                TipoNoExenta = 'S2'
                            else:
                                TipoNoExenta = 'S1'
                            taxes_sii['DesgloseFactura']['Sujeta']['NoExenta'][
                                'TipoNoExenta'] = TipoNoExenta
                            if 'DesgloseIVA' not in taxes_sii[
                                'DesgloseFactura']['Sujeta']['NoExenta']:
                                taxes_sii['DesgloseFactura']['Sujeta'][
                                    'NoExenta']['DesgloseIVA'] = {}
                                taxes_sii['DesgloseFactura']['Sujeta'][
                                    'NoExenta']['DesgloseIVA'][
                                    'DetalleIVA'] = []
                            tax_type = tax_line.amount * 100
                            if tax_type not in taxes_f:
                                taxes_f[str(tax_type)] = self._get_sii_tax_line(cr, uid,
                                    tax_line, line, line.invoice_line_tax_id,
                                    invoice)
                            else:
                                taxes_f = self._update_sii_tax_line(cr, uid,
                                    taxes_f, tax_line, line,
                                    line.invoice_line_tax_id,
                                    invoice)
                if tax_line.description in [
                    'S_IVA21S', 'S_IVA10S', 'S_IVA4S', 'S_IVA0']:
                    if 'DesgloseTipoOperacion' not in taxes_sii:
                        taxes_sii['DesgloseTipoOperacion'] = {}
                    if 'PrestacionServicios' not in taxes_sii[
                        'DesgloseTipoOperacion']:
                        taxes_sii['DesgloseTipoOperacion'][
                            'PrestacionServicios'] = {}
                    if 'Sujeta' not in taxes_sii['DesgloseTipoOperacion'][
                        'PrestacionServicios']:
                        taxes_sii['DesgloseTipoOperacion'][
                            'PrestacionServicios']['Sujeta'] = {}
                    if tax_line.description in ['']:
                        if 'Exenta' not in taxes_sii['DesgloseFactura'][
                            'Sujeta']:
                            taxes_sii['DesgloseFactura']['Sujeta'][
                                'Exenta'] = {
                                'BaseImponible': line.price_subtotal}
                        else:
                            taxes_sii['DesgloseFactura']['Sujeta'][
                                'Exenta']['BaeImponible'] += line.price_subtotal
                            #                     TODO Facturas no sujetas
                    if tax_line.description in [
                        'S_IVA21S', 'S_IVA10S', 'S_IVA4S']:
                        if 'NoExenta' not in taxes_sii['DesgloseTipoOperacion'][
                            'PrestacionServicios']['Sujeta']:
                            taxes_sii['DesgloseTipoOperacion'][
                                'PrestacionServicios']['Sujeta']['NoExenta'] = {}
                            #                             TODO l10n_es_ no tiene impuesto ISP de servicios
                            #                             if tax_line.description in ['S_IVA0S_ISP']:
                            #                                 TipoNoExenta = 'S2'
                            #                             else:
                            TipoNoExenta = 'S1'
                            taxes_sii['DesgloseTipoOperacion'][
                                'PrestacionServicios']['Sujeta']['NoExenta'][
                                'TipoNoExenta'] = TipoNoExenta
                        if 'DesgloseIVA' not in taxes_sii[
                            'DesgloseTipoOperacion']['PrestacionServicios'][
                            'Sujeta']['NoExenta']:
                            taxes_sii['DesgloseTipoOperacion'][
                                'PrestacionServicios']['Sujeta']['NoExenta'][
                                'DesgloseIVA'] = {}
                            taxes_sii['DesgloseTipoOperacion'][
                                'PrestacionServicios']['Sujeta']['NoExenta'][
                                'DesgloseIVA']['DetalleIVA'] = []
                            tax_type = tax_line.amount * 100
                            if tax_type not in taxes_to:
                                taxes_to[str(tax_type)] = self._get_sii_tax_line(cr, uid,
                                    tax_line, line, line.invoice_line_tax_id,
                                    invoice)
                            else:
                                taxes_to = self._update_sii_tax_line(
                                    taxes_to, tax_line, line,
                                    line.invoice_line_tax_id,
                                    invoice)

        if len(taxes_f) > 0:
            for key, line in taxes_f.iteritems():
                taxes_sii['DesgloseFactura']['Sujeta']['NoExenta'][
                    'DesgloseIVA']['DetalleIVA'].append(line)
        if len(taxes_to) > 0:
            for key, line in taxes_to.iteritems():
                taxes_sii['DesgloseTipoOperacion']['PrestacionServicios'][
                    'Sujeta']['NoExenta']['DesgloseIVA'][
                    'DetalleIVA'].append(line)

        return taxes_sii

    def _get_sii_in_taxes(self, cr, uid, invoice):
        taxes_sii = {}
        taxes_f = {}
        taxes_isp = {}
        for line in invoice.invoice_line:
            for tax_line in line.invoice_line_tax_id:
                if tax_line.description in [
                    'P_IVA21_BC', 'P_IVA21_SC', 'P_IVA21_ISP', 'P_IVA10_BC',
                    'P_IVA10_SC', 'P_IVA10_ISP', 'P_IVA4_BC', 'P_IVA4_SC',
                    'P_IVA4_ISP', 'P_IVA0_BC', 'P_IVA0_NS']:
                    if tax_line.description in [
                        'P_IVA21_ISP', 'P_IVA10_ISP', 'P_IVA4_ISP']:
                        if 'InversionSujetoPasivo' not in taxes_sii:
                            taxes_sii['InversionSujetoPasivo'] = {}
                            taxes_sii['InversionSujetoPasivo'][
                                'DetalleIVA'] = []
                        tax_type = tax_line.amount * 100
                        if tax_type not in taxes_isp:
                            taxes_isp[str(tax_type)] = self._get_sii_tax_line(cr, uid,
                                tax_line, line, line.invoice_line_tax_id,
                                invoice)
                        else:
                            taxes_isp = self._update_sii_tax_line(cr, uid,
                                taxes_isp, tax_line, line,
                                line.invoice_line_tax_id,
                                invoice)
                    else:
                        if 'DesgloseIVA' not in taxes_sii:
                            taxes_sii['DesgloseIVA'] = {}
                            taxes_sii['DesgloseIVA'][
                                'DetalleIVA'] = []
                        tax_type = tax_line.amount * 100
                        if tax_type not in taxes_f:
                            taxes_f[str(tax_type)] = self._get_sii_tax_line(cr, uid,
                                tax_line, line, line.invoice_line_tax_id,
                                invoice)
                        else:
                            taxes_f = self._update_sii_tax_line(cr, uid,
                                taxes_f, tax_line, line,
                                line.invoice_line_tax_id,
                                invoice)

        for key, line in taxes_f.iteritems():
            taxes_sii['DesgloseIVA']['DetalleIVA'].append(line)
        for key, line in taxes_isp.iteritems():
            taxes_sii['InversionSujetoPasivo']['DetalleIVA'].append(line)
        return taxes_sii

    def _get_invoices(self, cr, uid, company, invoice):
        invoice_date = self._change_date_format(cr, uid, invoice.date_invoice)
        Ejercicio = invoice.period_id.fiscalyear_id.date_start[0:4]
        Periodo = invoice.period_id.date_start[5:7]

        if invoice.type in ['out_invoice', 'out_refund']:
            TipoFactura = 'F1'
            #           TODO Los 5 tipos de facturas rectificativas
            if invoice.type == 'out_refund':
                TipoFactura = 'R4'
            TipoDesglose = self._get_sii_out_taxes(cr, uid, invoice)
            invoices = {
                "IDFactura": {
                    "IDEmisorFactura": {
                        "NIF": company.vat[2:]
                    },
                    "NumSerieFacturaEmisor": invoice.number,
                    "FechaExpedicionFacturaEmisor": invoice_date},
                "PeriodoImpositivo": {
                    "Ejercicio": Ejercicio,
                    "Periodo": Periodo
                },
                "FacturaExpedida": {
                    "TipoFactura": TipoFactura,
                    "ClaveRegimenEspecialOTrascendencia": "01",
                    "DescripcionOperacion": invoice.name,
                    "Contraparte": {
                        "NombreRazon": invoice.partner_id.name,
                        "NIF": invoice.partner_id.vat[2:]
                    },
                    "TipoDesglose": TipoDesglose
                }
            }
            if invoice.type == 'out_refund':
                invoices['FacturaExpedida'][
                    'TipoRectificativa'] = invoice.refund_type

        if invoice.type in ['in_invoice', 'in_refund']:
            #           TODO Los 5 tipos de facturas rectificativas
            TipoFactura = 'F1'
            if invoice.type == 'in_refund':
                TipoFactura = 'R4'
            DesgloseFactura = self._get_sii_in_taxes(cr, uid, invoice)
            invoices = {
                "IDFactura": {
                    "IDEmisorFactura": {
                        "NIF": invoice.partner_id.vat[2:]
                    },
                    "NumSerieFacturaEmisor": invoice.supplier_invoice_number,
                    "FechaExpedicionFacturaEmisor": invoice_date},
                "PeriodoImpositivo": {
                    "Ejercicio": Ejercicio,
                    "Periodo": Periodo
                },
                "FacturaRecibida": {
                    "TipoFactura": TipoFactura,
                    "ClaveRegimenEspecialOTrascendencia": "01",
                    "DescripcionOperacion": invoice.name,
                    "DesgloseFactura": DesgloseFactura,
                    "Contraparte": {
                        "NombreRazon": invoice.partner_id.name,
                        "NIF": invoice.partner_id.vat[2:]
                    },
                    "FechaRegContable": invoice_date,
                    "CuotaDeducible": invoice.amount_tax
                }
            }
            if invoice.type == 'in_refund':
                invoices['FacturaRecibida'][
                    'TipoRectificativa'] = invoice.refund_type

        return invoices

    def _connect_sii(self, cr, uid, wsdl):
        publicCrt = self.pool.get('ir.config_parameter').get_param(cr, uid,
            'l10n_es_aeat_sii.publicCrt', False)
        privateKey = self.pool.get('ir.config_parameter').get_param(cr, uid,
            'l10n_es_aeat_sii.privateKey', False)

        session = Session()
        session.cert = (publicCrt, privateKey)
        transport = Transport(session=session)

        history = HistoryPlugin()
        client = Client(wsdl=wsdl, transport=transport, plugins=[history])
        return client


    def _send_invoice_to_sii(self, cr, uid, ids):
        for invoice in self.pool.get('account.invoice').browse(cr, uid, ids):
            company = invoice.company_id
            port_name = ''

            fp_intra_id = self.pool.get('account.fiscal.position').search(cr, uid,
                                                                         [('name', '=', 'Régimen Intracomunitario')])

            if invoice.type in ['out_invoice', 'out_refund']:
                wsdl = company.wsdl_out
                client = self._connect_sii(cr, uid, wsdl)
                port_name = 'SuministroFactEmitidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            elif invoice.type in ['in_invoice', 'in_refund']:
                wsdl = company.wsdl_in
                client = self._connect_sii(cr, uid, wsdl)
                port_name = 'SuministroFactRecibidas'
                if company.sii_test:
                    port_name += 'Pruebas'
                    #             TODO Property Investiment
                    #             elif invoice == 'Property Investiment':
                    #                 wsdl = company.wsdl_pi
                    #                 client = self._connect_sii(wsdl)
                    #                 port_name = 'SuministroBienesInversion'
                    #                 if company.sii_test:
                    #                     port_name += 'Pruebas'
            elif invoice.fiscal_position.id == fp_intra_id:
                wsdl = company.wsdl_ic
                client = self._connect_sii(wsdl)
                port_name = 'SuministroOpIntracomunitarias'
                if company.sii_test:
                    port_name += 'Pruebas'

            serv = client.bind('siiService', port_name)

            if not invoice.sii_sent:
                TipoComunicacion = 'A0'
            else:
                TipoComunicacion = 'A1'

            header = self._get_header(cr, uid, invoice.id, company, TipoComunicacion)
            invoices = self._get_invoices(cr, uid, company, invoice)
            try:
                if invoice.type in ['out_invoice', 'out_refund']:
                    res = serv.SuministroLRFacturasEmitidas(
                        header, invoices)
                elif invoice.type in ['in_invoice', 'in_refund']:
                    res = serv.SuministroLRFacturasRecibidas(
                        header, invoices)
                    #                 TODO Factura Bienes de inversión
                    #                 elif invoice == 'Property Investiment':
                    #                     res = serv.SuministroLRBienesInversion(
                    #                         header, invoices)
                    #                 TODO Facturas intracomunitarias
                    #                 elif invoice.fiscal_position.id == self.env.ref(
                    #                     'account.fp_intra').id:
                    #                     res = serv.SuministroLRDetOperacionIntracomunitaria(
                    #                         header, invoices)
                if res['EstadoEnvio'] == 'Correcto':
                   self.write(cr, uid, invoice.id, {'sii_sent': True})
                self.write(cr, uid, invoice.id, {'sii_return': res})
            except Exception as fault:
                self.write(cr, uid, invoice.id, {'sii_return': fault})

    def action_number(self, cr, uid, ids, context=None):
        res = super(AccountInvoice, self).action_number(cr, uid, ids, context=context)
        self._send_invoice_to_sii(cr, uid, ids)

        return res
