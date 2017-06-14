# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Alberto Martín Cortada <alberto.martin@guadaltech.es>
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.osv import osv, fields
from openerp import exceptions
from requests import Session
from zeep import Client
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from datetime import datetime
from openerp.tools.translate import _


class AccountInvoice(osv.Model):
    _inherit = 'account.invoice'

    def _get_default_key(self, cr, uid, data, context=None):
        if context is None:
            context = {}

        sii_key_obj = self.pool['aeat.sii.mapping.registration.keys']
        type = context.get('type')
        if type in ['in_invoice', 'in_refund']:
            key = sii_key_obj.search(cr, uid,
                                     [('code', '=', '01'), ('type', '=', 'purchase')], limit=1)
        else:
            key = sii_key_obj.search(cr, uid,
                                     [('code', '=', '01'), ('type', '=', 'sale')], limit=1)
        return key and key[0]

    _columns = {

        'sii_description': fields.text(string='SII Description',
                                       required=True),
        'sii_sent': fields.boolean(string='SII Sent'),
        'sii_return': fields.text(string='SII Return'),
        'refund_type': fields.selection(
            selection=[('S', 'By substitution'), ('I', 'By differences')],
            string="Refund Type"),
        'registration_key': fields.many2one('aeat.sii.mapping.registration.keys', "Registration key", required=True),
        'sii_csv': fields.char(string='SII CSV', size=64),
        'sii_enabled': fields.related('company_id', 'sii_enabled', type='boolean', string='Enable SII'),

    }

    _defaults = {
        'registration_key': _get_default_key,
        'sii_description': '/',
    }

    def copy(self, cr, uid, id, default, context={}):

        default['sii_sent'] = False
        default['sii_return'] = None
        default['sii_csv'] = None

        return super(AccountInvoice, self).copy(cr, uid, id, default, context=context)

    def onchange_refund_type(self, cr, uid, ids, refund_type):
        for invoice in self.browse(cr, uid, ids):
            if refund_type == 'S' and not invoice.origin_invoices_ids:
                return {'warning':
                            {'message': 'Debes tener al menos una factura '
                                        'vinculada que sustituir'
                             },
                        'values': {
                            'refund_type':None,
                        }
                        }

    def map_tax_template(self, cr, uid, tax_template, mapping_taxes, invoice):
        # Adapted from account_chart_update module
        """Adds a tax template -> tax id to the mapping."""
        if not tax_template:
            return None
        if mapping_taxes.get(tax_template):
            return mapping_taxes[tax_template]
        # search inactive taxes too, to avoid re-creating
        # taxes that have been deactivated before
        context = {'active_test': False}
        tax_obj = self.pool['account.tax']
        criteria = ['|',
                    ('name', '=', tax_template.name),
                    ('description', '=', tax_template.name)]
        if tax_template.description:
            criteria = ['|', '|'] + criteria
            criteria += [('description', '=', tax_template.description),
                         ('name', '=', tax_template.description)]
        criteria += [('company_id', '=', invoice.company_id.id)]
        taxes = tax_obj.search(cr, uid, criteria, context=context)
        mapping_taxes[tax_template] = (
            taxes and taxes[0] or None)
        return mapping_taxes[tax_template]

    def _get_taxes_map(self, cr, uid, codes, date, invoice):
        # Return the codes that correspond to that sii map line codes
        taxes = []
        sii_map_obj = self.pool['aeat.sii.map']
        sii_map_line_obj = self.pool['aeat.sii.map.lines']
        sii_map = sii_map_obj.browse(cr, uid, sii_map_obj.search(cr, uid,
                                                                 ['|',
                                                                  ('date_from', '<=', date),
                                                                  ('date_from', '=', False),
                                                                  '|',
                                                                  ('date_to', '>=', date),
                                                                  ('date_to', '=', False)], limit=1)[0])
        mapping_taxes = {}
        for code in codes:
            map_line = sii_map_line_obj.search(cr, uid, [('code', '=', code), ('sii_map_id', '=', sii_map.id)], limit=1)
            if map_line:
                map_line = map_line[0]

            tax_templates = sii_map_line_obj.browse(cr, uid, map_line)
            if not tax_templates:
                continue

            tax_templates = tax_templates.taxes

            for tax_template in tax_templates:
                tax = self.map_tax_template(cr, uid, tax_template, mapping_taxes, invoice)
                if tax:
                    taxes.append(tax)
        return self.pool["account.tax"].browse(cr, uid, taxes)

    def _change_date_format(self, cr, uid, date):
        datetimeobject = datetime.strptime(date, '%Y-%m-%d')
        new_date = datetimeobject.strftime('%d-%m-%Y')
        return new_date

    def _get_header(self, cr, uid, ids, company, tipo_comunicacion):

        if not company.vat:
            raise exceptions.Warning(_(
                "No VAT configured for the company '{}'").format(company.name))
        id_version_sii = self.pool.get('ir.config_parameter').get_param(cr, uid,
                                                                        'l10n_es_aeat_sii.version', False)
        header = {
            "IDVersionSii": id_version_sii,
            "Titular": {
                "NombreRazon": company.name[0:120],
                "NIF": company.vat[2:]},
            "TipoComunicacion": tipo_comunicacion
        }
        return header

    def _get_line_price_subtotal(self, cr, uid, line):
        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        return price


    def _get_tax_line_req(self, cr, uid, tax_type, line, line_taxes):
        taxes = False
        taxes_RE = self._get_taxes_map(cr, uid,
                                       ['RE'], line.invoice_id.date_invoice, line.invoice_id)
        if len(line_taxes) > 1:
            for tax in line_taxes:
                if tax in taxes_RE:
                    price = self._get_line_price_subtotal(cr, uid, line)
                    taxes = self.pool.get('account.tax').compute_all(cr, uid, [tax],
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
            taxes = self.pool.get('account.tax').compute_all(cr, uid, [tax],
                                                             self._get_line_price_subtotal(cr, uid, line),
                                                             line.quantity, line.product_id, line.invoice_id.partner_id)

        tax_sii = {
            "TipoImpositivo": tax_type,
            "BaseImponible": taxes['total'],
        }
        if tax_line_req:
            tipo_recargo = tax_line_req['percentage'] * 100
            cuota_recargo = tax_line_req['taxes'][0]['amount']
            tax_sii['TipoRecargoEquivalencia'] = tipo_recargo
            tax_sii['CuotaRecargoEquivalencia'] = cuota_recargo

        if invoice.type in ['out_invoice', 'out_refund']:
            tax_sii['CuotaRepercutida'] = taxes['taxes'][0]['amount']
        if invoice.type in ['in_invoice', 'in_refund']:
            tax_sii['CuotaSoportada'] = taxes['taxes'][0]['amount']
        return tax_sii

    def _update_sii_tax_line(self, cr, uid, tax_sii, tax_line, line, line_taxes, invoice):
        tax_type = tax_line.amount * 100
        tax_line_req = self._get_tax_line_req(cr, uid, tax_type, line, line_taxes)
        taxes = self.pool.get('account.tax').compute_all(cr, uid, [tax_line.id],
                                                         self._get_line_price_subtotal(cr, uid, line),
                                                         line.quantity, line.product_id, line.invoice_id.partner_id)
        if tax_line_req:
            tipo_recargo = tax_line_req['percentage'] * 100
            cuota_recargo = tax_line_req['taxes'][0]['amount']
            tax_sii[str(tax_type)]['TipoRecargoEquivalencia'] += tipo_recargo
            tax_sii[str(tax_type)]['CuotaRecargoEquivalencia'] += cuota_recargo

        tax_sii[str(tax_type)]['BaseImponible'] += taxes['total']
        if invoice.type in ['out_invoice', 'out_refund']:
            taxes[str(tax_type)]['CuotaRepercutida'] += taxes['taxes'][0]['amount']
        if invoice.type in ['in_invoice', 'in_refund']:
            taxes[str(tax_type)]['CuotaSoportada'] += taxes['taxes'][0]['amount']
        return taxes

    def _get_sii_out_taxes(self, cr, uid, invoice):
        taxes_sii = {}
        taxes_f = {}
        taxes_to = {}
        taxes_sfesb = self._get_taxes_map(cr, uid,
                                          ['SFESB'], invoice.date_invoice, invoice)
        taxes_sfesbe = self._get_taxes_map(cr, uid,
                                           ['SFESBE'], invoice.date_invoice, invoice)
        taxes_sfesisp = self._get_taxes_map(cr, uid,
                                            ['SFESISP'], invoice.date_invoice, invoice)
        #         taxes_SFESISPS = self._get_taxes_map(cr, uid,
        #             ['SFESISPS'], invoice.date_invoice, invoice)
        taxes_sfens = self._get_taxes_map(cr, uid,
                                          ['SFENS'], invoice.date_invoice, invoice)
        taxes_sfess = self._get_taxes_map(cr, uid,
                                          ['SFESS'], invoice.date_invoice, invoice)
        taxes_sfesse = self._get_taxes_map(cr, uid,
                                           ['SFESSE'], invoice.date_invoice, invoice)
        for line in invoice.invoice_line:
            for tax_line in line.invoice_line_tax_id:

                if tax_line in taxes_sfesb or tax_line in taxes_sfesisp or \
                                tax_line in taxes_sfens:
                    if 'DesgloseFactura' not in taxes_sii:
                        taxes_sii['DesgloseFactura'] = {}
                    inv_breakdown = taxes_sii['DesgloseFactura']
                    if tax_line in taxes_sfesb:
                        if 'Sujeta' not in inv_breakdown:
                            inv_breakdown['Sujeta'] = {}
                        # TODO l10n_es no tiene impuesto exento de bienes
                        # corrientes nacionales
                        if tax_line in taxes_sfesbe:
                            if 'Exenta' not in inv_breakdown['Sujeta']:
                                inv_breakdown['Sujeta']['Exenta'] = {
                                    'BaseImponible': line.price_subtotal}
                            else:
                                inv_breakdown['Sujeta']['Exenta'][
                                    'BaseImponible'] += line.price_subtotal
                        # TODO Facturas No sujetas
                        if tax_line in taxes_sfesb or \
                                        tax_line in taxes_sfesisp:
                            if 'NoExenta' not in inv_breakdown[
                                'Sujeta']:
                                inv_breakdown['Sujeta'][
                                    'NoExenta'] = {}
                            if tax_line in taxes_sfesisp:
                                tipo_no_exenta = 'S2'
                            else:
                                tipo_no_exenta = 'S1'
                            inv_breakdown['Sujeta']['NoExenta'][
                                'TipoNoExenta'] = tipo_no_exenta
                            if 'DesgloseIVA' not in taxes_sii[
                                'DesgloseFactura']['Sujeta']['NoExenta']:
                                inv_breakdown['Sujeta'][
                                    'NoExenta']['DesgloseIVA'] = {}
                                inv_breakdown['Sujeta'][
                                    'NoExenta']['DesgloseIVA'][
                                    'DetalleIVA'] = []
                            tax_type = tax_line.amount * 100
                            if str(tax_type) not in taxes_f:
                                taxes_f[str(tax_type)] = self._get_sii_tax_line(cr, uid,
                                                                                tax_line, line,
                                                                                line.invoice_line_tax_id,
                                                                                invoice)
                            else:
                                taxes_f = self._update_sii_tax_line(cr, uid,
                                                                    taxes_f, tax_line, line,
                                                                    line.invoice_line_tax_id,
                                                                    invoice)

                if tax_line in taxes_sfess or tax_line in taxes_sfesse:
                    if 'DesgloseTipoOperacion' not in taxes_sii:
                        taxes_sii['DesgloseTipoOperacion'] = {}
                    type_breakdown = taxes_sii['DesgloseTipoOperacion']
                    if 'PrestacionServicios' not in type_breakdown:
                        type_breakdown['PrestacionServicios'] = {}
                    if 'Sujeta' not in type_breakdown['PrestacionServicios']:
                        type_breakdown['PrestacionServicios']['Sujeta'] = {}
                    if tax_line in taxes_sfesse:
                        if 'Exenta' not in taxes_sii['DesgloseTipoOperacion'][
                            'PrestacionServicios']['Sujeta']:
                            taxes_sii['DesgloseTipoOperacion'][
                                'PrestacionServicios']['Sujeta']['Exenta'] = {
                                'BaseImponible': line.price_subtotal}
                        else:
                            taxes_sii['DesgloseTipoOperacion'][
                                'PrestacionServicios']['Sujeta']['Exenta'][
                                'BaseImponible'] += line.price_subtotal
                    # TODO Facturas no sujetas
                    if tax_line in taxes_sfess:
                        if 'NoExenta' not in type_breakdown[
                            'PrestacionServicios']['Sujeta']:
                            type_breakdown['PrestacionServicios'][
                                'Sujeta']['NoExenta'] = {}
                            # TODO l10n_es_ no tiene impuesto ISP de servicios
                            # if tax_line in taxes_sfesisps:
                            #     TipoNoExenta = 'S2'
                            # else:
                            tipo_no_exenta = 'S1'
                            type_breakdown[
                                'PrestacionServicios']['Sujeta']['NoExenta'][
                                'TipoNoExenta'] = tipo_no_exenta
                        if 'DesgloseIVA' not in taxes_sii[
                            'DesgloseTipoOperacion']['PrestacionServicios'][
                            'Sujeta']['NoExenta']:
                            type_breakdown[
                                'PrestacionServicios']['Sujeta']['NoExenta'][
                                'DesgloseIVA'] = {}
                            type_breakdown[
                                'PrestacionServicios']['Sujeta']['NoExenta'][
                                'DesgloseIVA']['DetalleIVA'] = []
                            tax_type = tax_line.amount * 100
                            if str(tax_type) not in taxes_to:
                                taxes_to[str(tax_type)] = self._get_sii_tax_line(cr, uid,
                                                                                 tax_line, line,
                                                                                 line.invoice_line_tax_id,
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
        taxes_sfrs = self._get_taxes_map(cr, uid,
                                         ['SFRS'], invoice.date_invoice, invoice)
        taxes_sfrisp = self._get_taxes_map(cr, uid,
                                           ['SFRISP'], invoice.date_invoice, invoice)
        for line in invoice.invoice_line:
            for tax_line in line.invoice_line_tax_id:
                if tax_line in taxes_sfrs or tax_line in taxes_sfrisp:
                    if tax_line in taxes_sfrisp:
                        if 'InversionSujetoPasivo' not in taxes_sii:
                            taxes_sii['InversionSujetoPasivo'] = {}
                            taxes_sii['InversionSujetoPasivo'][
                                'DetalleIVA'] = []
                        tax_type = tax_line.amount * 100
                        if str(tax_type) not in taxes_isp:
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
                        if str(tax_type) not in taxes_f:
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

    def _get_invoices(self, cr, uid, invoice):
        invoice_date = self._change_date_format(cr, uid, invoice.date_invoice)
        company = invoice.company_id
        ejercicio = invoice.period_id.fiscalyear_id.date_start[0:4]
        periodo = invoice.period_id.date_start[5:7]

        if not company.chart_template_id:
            raise exceptions.Warning(_(
                'You have to select what account chart template use this'
                ' company.'))
        if invoice.type in ['out_invoice', 'out_refund']:
            tipo_factura = 'F1'
            #           TODO Los 5 tipos de facturas rectificativas
            if invoice.type == 'out_refund':
                tipo_factura = 'R4'
            tipo_desglose = self._get_sii_out_taxes(cr, uid, invoice)
            key = invoice.registration_key.code
            invoices = {
                "IDFactura": {
                    "IDEmisorFactura": {
                        "NIF": company.vat[2:]
                    },
                    "NumSerieFacturaEmisor": invoice.number[0:60],
                    "FechaExpedicionFacturaEmisor": invoice_date},
                "PeriodoImpositivo": {
                    "Ejercicio": ejercicio,
                    "Periodo": periodo
                },
                "FacturaExpedida": {
                    "TipoFactura": tipo_factura,
                    "ClaveRegimenEspecialOTrascendencia": key,
                    "DescripcionOperacion": invoice.sii_description[0:500],
                    "Contraparte": {
                        "NombreRazon": invoice.partner_id.name[0:120],
                        "NIF": invoice.partner_id.vat[2:]
                    },
                    "TipoDesglose": tipo_desglose,
                    "ImporteTotal": invoice.amount_total
                }
            }
            # Uso condicional de IDOtro/NIF
            invoices['FacturaExpedida']['Contraparte'].update(
                self._get_sii_identifier(cr, uid, invoice))

            if invoice.type == 'out_refund':
                invoices['FacturaExpedida'][
                    'TipoRectificativa'] = invoice.refund_type

                if invoice.refund_type == 'S':
                    base_rectificada = 0
                    cuota_rectificada = 0
                    for s in invoice.origin_invoices_ids:
                        base_rectificada += s.amount_untaxed
                        cuota_rectificada += s.amount_tax
                    invoices['FacturaExpedida']['ImporteRectificacion'] = {
                        'BaseRectificada': base_rectificada,
                        'CuotaRectificada': cuota_rectificada
                    }

        if invoice.type in ['in_invoice', 'in_refund']:
            #           TODO Los 5 tipos de facturas rectificativas
            tipo_factura = 'F1'
            if invoice.type == 'in_refund':
                tipo_factura = 'R4'
            desglose_factura = self._get_sii_in_taxes(cr, uid, invoice)
            invoices = {
                "IDFactura": {
                    "IDEmisorFactura": {
                        "NIF": invoice.partner_id.vat[2:]
                    },
                    "NumSerieFacturaEmisor": invoice.reference[0:60],
                    "FechaExpedicionFacturaEmisor": invoice_date},
                "PeriodoImpositivo": {
                    "Ejercicio": ejercicio,
                    "Periodo": periodo
                },
                "FacturaRecibida": {
                    "TipoFactura": tipo_factura,
                    "ClaveRegimenEspecialOTrascendencia": "01",
                    "DescripcionOperacion": invoice.sii_description[0:500],
                    "DesgloseFactura": desglose_factura,
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
                if invoice.refund_type == 'S':
                    base_rectificada = 0
                    cuota_rectificada = 0
                    for s in invoice.origin_invoices_ids:
                        base_rectificada += s.amount_untaxed
                        cuota_rectificada += s.amount_tax
                    invoices['FacturaRecibida']['ImporteRectificacion'] = {
                        'BaseRectificada': base_rectificada,
                        'CuotaRectificada': cuota_rectificada
                    }
        return invoices

    def _connect_sii(self, cr, uid, wsdl, company):

        today = datetime.today()
        config_obj = self.pool.get('l10n.es.aeat.sii')
        sii_config_ids = config_obj.search(cr, uid,[
            ('company_id', '=', company.id),
            ('public_key', '!=', False),
            ('private_key', '!=', False),
            '|', ('date_start', '=', False),
            ('date_start', '<=', today),
            '|', ('date_end', '=', False),
            ('date_end', '>=', today),
            ('state', '=', 'active')
        ], limit=1)

        if sii_config_ids:
            sii_config = config_obj.browse(cr, uid, sii_config_ids[0])
            public_crt = sii_config.public_key
            private_key = sii_config.private_key
        else:
            public_crt = self.pool.get('ir.config_parameter').get_param(cr, uid,
                                                                       'l10n_es_aeat_sii.publicCrt', False)
            private_key = self.pool.get('ir.config_parameter').get_param(cr, uid,
                                                                        'l10n_es_aeat_sii.privateKey', False)

        session = Session()
        session.cert = (public_crt, private_key)
        transport = Transport(session=session)

        history = HistoryPlugin()
        client = Client(wsdl=wsdl, transport=transport, plugins=[history])
        return client

    def _send_invoice_to_sii(self, cr, uid, ids):
        for invoice in self.pool.get('account.invoice').browse(cr, uid, ids):
            company = invoice.company_id
            port_name = ''
            if invoice.type in ['out_invoice', 'out_refund']:
                wsdl = self.pool['ir.config_parameter'].get_param(cr, uid,
                                                                  'l10n_es_aeat_sii.wsdl_out', False)
                client = self._connect_sii(cr, uid, wsdl, company)
                port_name = 'SuministroFactEmitidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            elif invoice.type in ['in_invoice', 'in_refund']:
                wsdl = self.pool['ir.config_parameter'].get_param(cr, uid,
                                                                  'l10n_es_aeat_sii.wsdl_in', False)
                client = self._connect_sii(cr, uid, wsdl, company)
                port_name = 'SuministroFactRecibidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            serv = client.bind('siiService', port_name)
            if not invoice.sii_sent:
                tipo_comunicacion = 'A0'
            else:
                tipo_comunicacion = 'A1'
            header = self._get_header(cr, uid, invoice.id, company, tipo_comunicacion)
            invoices = self._get_invoices(cr, uid, invoice)
            try:
                if invoice.type in ['out_invoice', 'out_refund']:
                    res = serv.SuministroLRFacturasEmitidas(
                        header, invoices)
                elif invoice.type in ['in_invoice', 'in_refund']:
                    res = serv.SuministroLRFacturasRecibidas(
                        header, invoices)
                # TODO Facturas intracomunitarias 66 RIVA
                # elif invoice.fiscal_position.id == self.env.ref(
                #     'account.fp_intra').id:
                #     res = serv.SuministroLRDetOperacionIntracomunitaria(
                #         header, invoices)
                if res['EstadoEnvio'] == 'Correcto':
                    self.write(cr, uid, invoice.id, {'sii_sent': True,
                                                     'sii_csv': res['CSV']
                                                     })
                self.write(cr, uid, invoice.id, {'sii_return': res})
            except Exception as fault:
                self.write(cr, uid, invoice.id, {'sii_return': fault})

    def action_number(self, cr, uid, ids, context=None):
        res = super(AccountInvoice, self).action_number(cr, uid, ids, context=context)
        for invoice in self.browse(cr, uid, ids):
            company = invoice.company_id
            if company.sii_enabled and company.sii_method == 'auto':
                self._send_invoice_to_sii(cr, uid, [invoice.id])

        return res

    def send_sii(self, cr, uid, ids, context=None):
        for invoice in self.browse(cr, uid, ids, context):
            company = invoice.company_id
            if company.sii_enabled:
                self._send_invoice_to_sii(cr, uid, [invoice.id])
        return True

    # @api.multi
    # def action_cancel(self):
    #     for queue in self.invoice_jobs_ids:
    #         if queue.state == 'started':
    #             raise Warning(_(
    #                 'You can not cancel this invoice because'
    #                 ' there is a job running!'))
    #         elif queue.state in ('pending', 'enqueued', 'failed'):
    #             queue.write({
    #                 'state': 'done',
    #                 'date_done': date.today()})
    #     return super(AccountInvoice, self).action_cancel()


    def _get_sii_identifier(self, cr, uid, invoice):
        codPais = invoice.partner_id.vat[:2]
        dic_ret = {}
        if codPais != 'ES':
            if invoice.fiscal_position.name == u'Régimen Intracomunitario':
                idType = '02'
            else:
                idType = '04'
            dic_ret = {
                "IDOtro": {
                    "CodigoPais": codPais,
                    "IDType": idType,
                    "ID": invoice.partner_id.vat
                }
            }
        else:
            dic_ret = {"NIF": invoice.partner_id.vat[2:]}
        return dic_ret
