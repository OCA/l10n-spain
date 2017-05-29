# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# (c) 2017 Consultoría Informática Studio 73 S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from requests import Session
from zeep import Client
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from datetime import datetime
from openerp.exceptions import Warning


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _get_default_key(self):
        sii_key_obj = self.env['aeat.sii.mapping.registration.keys']
        type = self._context.get('type')
        if type in ['in_invoice', 'in_refund']:
            key = sii_key_obj.search(
                [('code', '=', '01'), ('type', '=', 'purchase')], limit=1)
        else:
            key = sii_key_obj.search(
                [('code', '=', '01'), ('type', '=', 'sale')], limit=1)
        return key

    sii_description = fields.Text(string='SII Description')
    sii_sent = fields.Boolean(string='SII Sent')
    sii_csv = fields.Char(string='SII CSV')
    sii_return = fields.Text(string='SII Return')
    refund_type = fields.Selection(
        selection=[('S', 'By substitution'), ('I', 'By differences')],
        string="Refund Type")
    registration_key = fields.Many2one(
        comodel_name='aeat.sii.mapping.registration.keys',
        string="Registration key", required=True, default=_get_default_key)
    sii_enabled = fields.Boolean(string='Enable SII',
                                 related='company_id.sii_enabled')

    @api.multi
    def map_tax_template(self, tax_template, mapping_taxes):
        # Adapted from account_chart_update module
        """Adds a tax template -> tax id to the mapping."""
        if not tax_template:
            return self.env['account.tax']
        if mapping_taxes.get(tax_template):
            return mapping_taxes[tax_template]
        # search inactive taxes too, to avoid re-creating
        # taxes that have been deactivated before
        tax_obj = self.env['account.tax'].with_context(active_test=False)
        criteria = ['|',
                    ('name', '=', tax_template.name),
                    ('description', '=', tax_template.name)]
        if tax_template.description:
            criteria = ['|', '|'] + criteria
            criteria += [('description', '=', tax_template.description),
                         ('name', '=', tax_template.description)]
        criteria += [('company_id', '=', self.company_id.id)]
        taxes = tax_obj.search(criteria)
        mapping_taxes[tax_template] = (
            taxes and taxes[0] or self.env['account.tax'])
        return mapping_taxes[tax_template]

    @api.multi
    def _get_taxes_map(self, codes, date):
        # Return the codes that correspond to that sii map line codes
        taxes = []
        sii_map_obj = self.env['aeat.sii.map']
        sii_map_line_obj = self.env['aeat.sii.map.lines']
        sii_map = sii_map_obj.search(
            ['|',
             ('date_from', '<=', date),
             ('date_from', '=', False),
             '|',
             ('date_to', '>=', date),
             ('date_to', '=', False)], limit=1)
        mapping_taxes = {}
        for code in codes:
            tax_templates = sii_map_line_obj.search(
                [('code', '=', code), ('sii_map_id', '=', sii_map.id)],
                limit=1).taxes
            for tax_template in tax_templates:
                tax = self.map_tax_template(tax_template, mapping_taxes)
                if tax:
                    taxes.append(tax)
        return taxes

    @api.multi
    def _change_date_format(self, date):
        datetimeobject = datetime.strptime(date,'%Y-%m-%d')
        new_date = datetimeobject.strftime('%d-%m-%Y')
        return new_date
    
    @api.multi
    def _get_header(self, company, TipoComunicacion):
        IDVersionSii = self.env['ir.config_parameter'].get_param(
            'l10n_es_aeat_sii.version', False)
        header = {
            "IDVersionSii": IDVersionSii,
            "Titular": {
                "NombreRazon": company.name[0:120],
                "NIF": company.vat[2:]},
            "TipoComunicacion": TipoComunicacion
        }
        return header
    
    @api.multi
    def _get_tax_line_req(self, tax_type, line, line_taxes):
        taxes = False
        taxes_RE = self._get_taxes_map(
            ['RE'], line.invoice_id.date_invoice)
        if len(line_taxes) > 1:
            for tax in line_taxes:
                if tax in taxes_RE:
                    price = line.price_unit * (1 - (
                        line.discount or 0.0) / 100.0)
                    taxes = tax.compute_all(
                        price, line.quantity, line.product_id,
                        line.invoice_id.partner_id)
                    taxes['percentage'] = tax.amount
                    return taxes
        return taxes
    
    @api.multi
    def _get_sii_tax_line(self, tax_line, line, line_taxes, invoice):
        tax_type = tax_line.amount * 100
        tax_line_req = self._get_tax_line_req(tax_type, line, line_taxes)
        taxes = tax_line.compute_all(
            (line.price_unit * (1 - (line.discount or 0.0) / 100.0)),
            line.quantity, line.product_id, line.invoice_id.partner_id)
        tax_sii = {
            "TipoImpositivo":tax_type,
            "BaseImponible":taxes['total']
        }
        if tax_line_req:
            TipoRecargo = tax_line_req['percentage'] * 100
            CuotaRecargo = tax_line_req['taxes'][0]['amount']
            tax_sii['TipoRecargoEquivalencia'] = TipoRecargo
            tax_sii['CuotaRecargoEquivalencia'] = CuotaRecargo

        if invoice.type in ['out_invoice', 'out_refund']:
            tax_sii['CuotaRepercutida'] = taxes['taxes'][0]['amount']
        if invoice.type in ['in_invoice', 'in_refund']:
            tax_sii['CuotaSoportada'] = taxes['taxes'][0]['amount']        
        return tax_sii
    
    @api.multi
    def _update_sii_tax_line(self, taxes, tax_line, line, line_taxes, invoice):
        tax_type = tax_type = tax_line.amount * 100
        tax_line_req = self._get_tax_line_req(tax_type, line, line_taxes)
        taxes = tax_line.compute_all(
            (line.price_unit * (1 - (line.discount or 0.0) / 100.0)),
            line.quantity, line.product_id, line.invoice_id.partner_id)
        if tax_line_req:
            TipoRecargo = tax_line_req['percentage'] * 100
            CuotaRecargo = tax_line_req['taxes'][0]['amount']
            taxes[str(tax_type)]['TipoRecargoEquivalencia'] += TipoRecargo
            taxes[str(tax_type)]['CuotaRecargoEquivalencia'] += CuotaRecargo

        taxes[str(tax_type)]['BaseImponible'] += taxes['total']
        if invoice.type in ['out_invoice', 'out_refund']:
            tax_sii['CuotaRepercutida'] += taxes['taxes'][0]['amount']
        if invoice.type in ['in_invoice', 'in_refund']:
            tax_sii['CuotaSoportada'] += taxes['taxes'][0]['amount'] 
        return taxes

    @api.multi
    def _get_sii_out_taxes(self, invoice):
        taxes_sii = {}
        taxes_f = {}
        taxes_to = {}
        taxes_SFESB = self._get_taxes_map(
            ['SFESB'], invoice.date_invoice)
        taxes_SFESBE = self._get_taxes_map(
            ['SFESBE'], invoice.date_invoice)
        taxes_SFESISP = self._get_taxes_map(
            ['SFESISP'], invoice.date_invoice)
#         taxes_SFESISPS = self._get_taxes_map(
#             ['SFESISPS'], invoice.date_invoice)
        taxes_SFENS = self._get_taxes_map(
            ['SFENS'], invoice.date_invoice)
        taxes_SFESS = self._get_taxes_map(
            ['SFESS'], invoice.date_invoice)
        taxes_SFESSE = self._get_taxes_map(
            ['SFESSE'], invoice.date_invoice)
        for line in invoice.invoice_line:
            for tax_line in line.invoice_line_tax_id:
                if (tax_line in taxes_SFESB or tax_line in taxes_SFESISP or
                    tax_line in taxes_SFENS):
                    if 'DesgloseFactura' not in taxes_sii:
                        taxes_sii['DesgloseFactura'] = {}
                    if tax_line in taxes_SFESB:
                        if 'Sujeta' not in taxes_sii['DesgloseFactura']:
                            taxes_sii['DesgloseFactura']['Sujeta'] = {}
#                   TODO l10n_es no tiene impuesto exento de bienes corrientes
#                   nacionales
                        if tax_line in taxes_SFESBE:
                            if 'Exenta' not in taxes_sii['DesgloseFactura'][
                                'Sujeta']:
                                taxes_sii['DesgloseFactura']['Sujeta'][
                                    'Exenta'] = {'BaseImponible': line.price_subtotal}
                            else:
                                taxes_sii['DesgloseFactura']['Sujeta'][
                                    'Exenta']['BaseImponible'] += line.price_subtotal
#                   TODO Facturas No sujetas
                        if tax_line in taxes_SFESB or tax_line in taxes_SFESISP:
                            if 'NoExenta' not in taxes_sii['DesgloseFactura'][
                                'Sujeta']:
                                taxes_sii['DesgloseFactura']['Sujeta'][
                                    'NoExenta'] = {}
                            if tax_line in taxes_SFESISP:
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
                                taxes_f[str(tax_type)] = self._get_sii_tax_line(
                                    tax_line, line, line.invoice_line_tax_id,
                                    invoice)
                            else:
                                taxes_f = self._update_sii_tax_line(
                                    taxes_f, tax_line, line,
                                    line.invoice_line_tax_id,
                                    invoice)
                if tax_line in taxes_SFESS or tax_line in taxes_SFESSE:
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
                    if tax_line in taxes_SFESSE:
                        if 'Exenta' not in taxes_sii['DesgloseFactura'][
                            'Sujeta']:
                            taxes_sii['DesgloseFactura']['Sujeta'][
                                'Exenta'] = {
                                    'BaseImponible': line.price_subtotal}
                        else:
                            taxes_sii['DesgloseFactura']['Sujeta'][
                                'Exenta']['BaeImponible'] += line.price_subtotal
#                     TODO Facturas no sujetas
                    if tax_line in taxes_SFESS:
                        if 'NoExenta' not in taxes_sii['DesgloseTipoOperacion'][
                            'PrestacionServicios']['Sujeta']:
                            taxes_sii['DesgloseTipoOperacion'][
                            'PrestacionServicios']['Sujeta']['NoExenta'] = {}
#                             TODO l10n_es_ no tiene impuesto ISP de servicios
#                             if tax_line in taxes_SFESISPS:
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
                                taxes_to[str(tax_type)] = self._get_sii_tax_line(
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

    @api.multi
    def _get_sii_in_taxes(self, invoice): 
        taxes_sii = {}
        taxes_f = {}
        taxes_isp = {}
        taxes_SFRS = self._get_taxes_map(
            ['SFRS'], invoice.date_invoice)
        taxes_SFRISP = self._get_taxes_map(
            ['SFRISP'], invoice.date_invoice)
        for line in invoice.invoice_line:
            for tax_line in line.invoice_line_tax_id:
                if tax_line in taxes_SFRS or tax_line in taxes_SFRISP:
                    if tax_line in taxes_SFRISP:
                        if 'InversionSujetoPasivo' not in taxes_sii:
                            taxes_sii['InversionSujetoPasivo'] = {}
                            taxes_sii['InversionSujetoPasivo'][
                                'DetalleIVA'] = []
                        tax_type = tax_line.amount * 100
                        if tax_type not in taxes_isp:
                            taxes_isp[str(tax_type)] = self._get_sii_tax_line(
                                tax_line, line, line.invoice_line_tax_id,
                                invoice)
                        else:
                            taxes_isp = self._update_sii_tax_line(
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
                            taxes_f[str(tax_type)] = self._get_sii_tax_line(
                                tax_line, line, line.invoice_line_tax_id,
                                invoice)
                        else:
                            taxes_f = self._update_sii_tax_line(
                                taxes_f, tax_line, line,
                                line.invoice_line_tax_id,
                                invoice)

        for key, line in taxes_f.iteritems():
            taxes_sii['DesgloseIVA']['DetalleIVA'].append(line)
        for key, line in taxes_isp.iteritems():
            taxes_sii['InversionSujetoPasivo']['DetalleIVA'].append(line)
        return taxes_sii
                    
    
    @api.multi
    def _get_invoices(self, company, invoice):
        invoice_date = self._change_date_format(invoice.date_invoice)
        Ejercicio = fields.Date.from_string(
            invoice.period_id.fiscalyear_id.date_start).year
        Periodo = '%02d' % fields.Date.from_string(
            invoice.period_id.date_start).month
        if not company.chart_template_id:
            raise Warning(_(
                'You have to select what account chart template use this'
                ' company.'))
        if invoice.type in ['out_invoice', 'out_refund']:
            TipoFactura = 'F1'
#           TODO Los 5 tipos de facturas rectificativas
            if invoice.type == 'out_refund':
                TipoFactura = 'R4'
            TipoDesglose = self._get_sii_out_taxes(invoice)
            key = invoice.registration_key.code
            invoices = {
                "IDFactura":{
                    "IDEmisorFactura": {
                        "NIF": company.vat[2:]
                        },
                    "NumSerieFacturaEmisor": invoice.number[0:60],
                    "FechaExpedicionFacturaEmisor": invoice_date},
                "PeriodoImpositivo": {
                    "Ejercicio": Ejercicio,
                    "Periodo": Periodo
                    },
                "FacturaExpedida": {
                    "TipoFactura": TipoFactura,
                    "ClaveRegimenEspecialOTrascendencia": key,
                    "DescripcionOperacion": invoice.name,
                    "Contraparte": {
                        "NombreRazon": invoice.partner_id.name[0:120],
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
            DesgloseFactura = self._get_sii_in_taxes(invoice)
            invoices = {
                "IDFactura":{
                    "IDEmisorFactura": {
                        "NIF": invoice.partner_id.vat[2:]
                        },
                    "NumSerieFacturaEmisor": invoice.supplier_invoice_number[
                        0:60],
                    "FechaExpedicionFacturaEmisor": invoice_date},
                "PeriodoImpositivo": {
                    "Ejercicio": Ejercicio,
                    "Periodo": Periodo
                    },
                "FacturaRecibida": {
                    "TipoFactura": TipoFactura,
                    "ClaveRegimenEspecialOTrascendencia": "01",
                    "DescripcionOperacion": invoice.sii_description[0:500],
                    "DesgloseFactura": DesgloseFactura,
                    "Contraparte": {
                        "NombreRazon": invoice.partner_id.name[0:120],
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
    
    @api.multi
    def _connect_sii(self, wsdl):
        today = fields.Date.today()
        sii_config = self.env['l10n.es.aeat.sii'].search(
            [('company_id', '=', self.company_id.id),
             ('public_key', '!=', False),
             ('private_key', '!=', False),
             '|', ('date_start', '=', False),
             ('date_start', '<=', today),
             '|', ('date_end', '=', False),
             ('date_end', '>=', today),
             ('active', '=', True)],
            limit=1
        )
        if not sii_config:
            raise Warning(u'No hay un SII correctamente configurado para la '
                          u'compañia %s' % self.company_id.name_get()[0][1])
        
        session = Session()
        session.cert = (sii_config.public_key, sii_config.private_key)
        transport = Transport(session=session)

        history = HistoryPlugin()
        client = Client(wsdl=wsdl, transport=transport, plugins=[history])
        return client

    @api.multi
    def _send_invoice_to_sii(self):
        for invoice in self:
            company = invoice.company_id
            port_name = ''
            if invoice.type == 'out_invoice':
                wsdl = self.env['ir.config_parameter'].get_param(
                    'l10n_es_aeat_sii.wsdl_out', False)
                client = self._connect_sii(wsdl)
                port_name = 'SuministroFactEmitidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            elif invoice.type == 'in_invoice':
                wsdl = self.env['ir.config_parameter'].get_param(
                    'l10n_es_aeat_sii.wsdl_in', False)
                client = self._connect_sii(wsdl)
                port_name = 'SuministroFactRecibidas'
                if company.sii_test:
                    port_name += 'Pruebas'               
            serv = client.bind('siiService', port_name)
            if not invoice.sii_sent:
                TipoComunicacion = 'A0'
            else:
                TipoComunicacion = 'A1'
            
            header = self._get_header(company, TipoComunicacion)
            invoices = self._get_invoices(company, invoice)
            try:
                if invoice.type in ['out_invoice', 'out_refund']:
                    res = serv.SuministroLRFacturasEmitidas(
                        header, invoices)
                elif invoice.type in ['in_invoice', 'in_refund']:
                    res = serv.SuministroLRFacturasRecibidas(
                        header, invoices)
#                 TODO Facturas intracomunitarias 66 RIVA
#                 elif invoice.fiscal_position.id == self.env.ref(
#                     'account.fp_intra').id:
#                     res = serv.SuministroLRDetOperacionIntracomunitaria(
#                         header, invoices)
                if res['EstadoEnvio'] == 'Correcto':
                    self.sii_sent = True
                    self.sii_csv = res['CSV']
                else:
                    self.sii_sent = False
                self.sii_return = res
            except Exception as fault:
                self.sii_return = fault

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        
        if self.company_id.sii_enabled:
            if not self.company_id.use_connector:
                self._send_invoice_to_sii()
#             TODO 
#             else:
#                 Use connector
        
        return res
