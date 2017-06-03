# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# (c) 2017 Studio73 - Pablo Fuentes <pablo@studio73>
# (c) 2017 Studio73 - Jordi Tolsà <jordi@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from datetime import datetime, date
from requests import Session

from zeep import Client
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin

from openerp import models, fields, api, _
from openerp.exceptions import Warning


_logger = logging.getLogger(__name__)

try:
    from openerp.addons.connector.queue.job import job
    from openerp.addons.connector.session import ConnectorSession
except ImportError:
    _logger.debug('Can not `import connector`.')
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial
    job = empty_decorator_factory


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

    sii_description = fields.Text(
        'SII Description',
        default="/",
        required=True)
    sii_sent = fields.Boolean(string='SII Sent')
    sii_csv = fields.Char(string='SII CSV')
    sii_return = fields.Text(string='SII Return')
    refund_type = fields.Selection(
        selection=[('S', 'By substitution'), ('I', 'By differences')],
        default='I',
        string="Refund Type")
    registration_key = fields.Many2one(
        comodel_name='aeat.sii.mapping.registration.keys',
        string="Registration key", required=True, default=_get_default_key)
    sii_enabled = fields.Boolean(string='Enable SII',
                                 related='company_id.sii_enabled')
    invoice_jobs_ids = fields.Many2many(
        'queue.job',
        'invoice_id',
        'job_id',
        string="Invoice Jobs")

    @api.onchange('refund_type')
    def onchange_refund_type(self):
        if self.refund_type == 'S' and not self.origin_invoices_ids:
            self.refund_type = False
            return {'warning':
                {'message': 'Debes tener al menos una factura '
                            'vinculada que sustituir'
                 }
            }

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
        datetimeobject = datetime.strptime(date, '%Y-%m-%d')
        new_date = datetimeobject.strftime('%d-%m-%Y')
        return new_date

    @api.multi
    def _get_header(self, tipo_comunicacion):
        self.ensure_one()
        company = self.company_id
        if not company.vat:
            raise Warning(_(
                "No VAT configured for the company '{}'").format(company.name))
        id_version_sii = self.env['ir.config_parameter'].get_param(
            'l10n_es_aeat_sii.version', False)
        header = {
            "IDVersionSii": id_version_sii,
            "Titular": {
                "NombreRazon": self.company_id.name[0:120],
                "NIF": self.company_id.vat[2:]},
            "TipoComunicacion": tipo_comunicacion
        }
        return header

    @api.multi
    def _get_tax_line_req(self, tax_type, line, line_taxes):
        self.ensure_one()
        taxes = False
        taxes_re = self._get_taxes_map(
            ['RE'], line.invoice_id.date_invoice)
        if len(line_taxes) > 1:
            for tax in line_taxes:
                if tax in taxes_re:
                    price = line.price_unit * (1 - (
                        line.discount or 0.0) / 100.0)
                    taxes = tax.compute_all(
                        price, line.quantity, line.product_id,
                        line.invoice_id.partner_id)
                    taxes['percentage'] = tax.amount
                    return taxes
        return taxes

    @api.multi
    def _get_sii_tax_line(self, tax_line, line, line_taxes):
        self.ensure_one()
        tax_type = tax_line.amount * 100
        tax_line_req = self._get_tax_line_req(tax_type, line, line_taxes)
        taxes = tax_line.compute_all(
            (line.price_unit * (1 - (line.discount or 0.0) / 100.0)),
            line.quantity, line.product_id, line.invoice_id.partner_id)
        tax_sii = {
            "TipoImpositivo": tax_type,
            "BaseImponible": taxes['total']
        }
        if tax_line_req:
            tipo_recargo = tax_line_req['percentage'] * 100
            cuota_recargo = tax_line_req['taxes'][0]['amount']
            tax_sii['TipoRecargoEquivalencia'] = tipo_recargo
            tax_sii['CuotaRecargoEquivalencia'] = cuota_recargo

        if self.type in ['out_invoice', 'out_refund']:
            tax_sii['CuotaRepercutida'] = taxes['taxes'][0]['amount']
        if self.type in ['in_invoice', 'in_refund']:
            tax_sii['CuotaSoportada'] = taxes['taxes'][0]['amount']
        return tax_sii

    @api.multi
    def _update_sii_tax_line(self, tax_sii, tax_line, line, line_taxes):
        self.ensure_one()
        tax_type = tax_type = tax_line.amount * 100
        tax_line_req = self._get_tax_line_req(tax_type, line, line_taxes)
        taxes = tax_line.compute_all(
            (line.price_unit * (1 - (line.discount or 0.0) / 100.0)),
            line.quantity, line.product_id, line.invoice_id.partner_id)
        if tax_line_req:
            tipo_recargo = tax_line_req['percentage'] * 100
            cuota_recargo = tax_line_req['taxes'][0]['amount']
            tax_sii[str(tax_type)]['TipoRecargoEquivalencia'] += tipo_recargo
            tax_sii[str(tax_type)]['CuotaRecargoEquivalencia'] += cuota_recargo

        tax_sii[str(tax_type)]['BaseImponible'] += taxes['total']
        if self.type in ['out_invoice', 'out_refund']:
            tax_sii[str(tax_type)]['CuotaRepercutida'] += taxes['taxes'][0]['amount']
        if self.type in ['in_invoice', 'in_refund']:
            tax_sii[str(tax_type)]['CuotaSoportada'] += taxes['taxes'][0]['amount']
        return tax_sii

    @api.multi
    def _get_sii_out_taxes(self):
        self.ensure_one()
        taxes_sii = {}
        taxes_f = {}
        taxes_to = {}
        taxes_sfesb = self._get_taxes_map(['SFESB'], self.date_invoice)
        taxes_sfesbe = self._get_taxes_map(['SFESBE'], self.date_invoice)
        taxes_sfesisp = self._get_taxes_map(['SFESISP'], self.date_invoice)
        # taxes_sfesisps = self._get_taxes_map(['SFESISPS'], self.date_invoice)
        taxes_sfens = self._get_taxes_map(['SFENS'], self.date_invoice)
        taxes_sfess = self._get_taxes_map(['SFESS'], self.date_invoice)
        taxes_sfesse = self._get_taxes_map(['SFESSE'], self.date_invoice)
        for line in self.invoice_line:
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
                                taxes_f[str(tax_type)] = \
                                    self._get_sii_tax_line(
                                        tax_line, line,
                                        line.invoice_line_tax_id)
                            else:
                                taxes_f = self._update_sii_tax_line(
                                    taxes_f, tax_line, line,
                                    line.invoice_line_tax_id)
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
                                'PrestacionServicios']['º']['NoExenta'][
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
                                taxes_to[str(tax_type)] = \
                                    self._get_sii_tax_line(
                                        tax_line, line,
                                        line.invoice_line_tax_id)
                            else:
                                taxes_to = self._update_sii_tax_line(
                                    taxes_to, tax_line, line,
                                    line.invoice_line_tax_id)
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
    def _get_sii_in_taxes(self):
        self.ensure_one()
        taxes_sii = {}
        taxes_f = {}
        taxes_isp = {}
        taxes_sfrs = self._get_taxes_map(['SFRS'], self.date_invoice)
        taxes_sfrisp = self._get_taxes_map(['SFRISP'], self.date_invoice)
        for line in self.invoice_line:
            for tax_line in line.invoice_line_tax_id:
                if tax_line in taxes_sfrs or tax_line in taxes_sfrisp:
                    if tax_line in taxes_sfrisp:
                        if 'InversionSujetoPasivo' not in taxes_sii:
                            taxes_sii['InversionSujetoPasivo'] = {}
                            taxes_sii['InversionSujetoPasivo'][
                                'DetalleIVA'] = []
                        tax_type = tax_line.amount * 100
                        if str(tax_type) not in taxes_isp:
                            taxes_isp[str(tax_type)] = self._get_sii_tax_line(
                                tax_line, line, line.invoice_line_tax_id)
                        else:
                            taxes_isp = self._update_sii_tax_line(
                                taxes_isp, tax_line, line,
                                line.invoice_line_tax_id)
                    else:
                        if 'DesgloseIVA' not in taxes_sii:
                            taxes_sii['DesgloseIVA'] = {}
                            taxes_sii['DesgloseIVA'][
                                'DetalleIVA'] = []
                        tax_type = tax_line.amount * 100
                        if str(tax_type) not in taxes_f:
                            taxes_f[str(tax_type)] = self._get_sii_tax_line(
                                tax_line, line, line.invoice_line_tax_id)
                        else:
                            taxes_f = self._update_sii_tax_line(
                                taxes_f, tax_line, line,
                                line.invoice_line_tax_id)
        for key, line in taxes_f.iteritems():
            taxes_sii['DesgloseIVA']['DetalleIVA'].append(line)
        for key, line in taxes_isp.iteritems():
            taxes_sii['InversionSujetoPasivo']['DetalleIVA'].append(line)
        return taxes_sii

    @api.multi
    def _get_invoices(self):
        self.ensure_one()
        if not self.partner_id.vat:
            raise Warning(_(
                "The partner '{}' has not a VAT configured.").format(
                    self.partner_id.name))
        invoice_date = self._change_date_format(self.date_invoice)
        company = self.company_id
        ejercicio = fields.Date.from_string(
            self.period_id.fiscalyear_id.date_start).year
        periodo = '%02d' % fields.Date.from_string(
            self.period_id.date_start).month
        if not company.chart_template_id:
            raise Warning(_(
                'You have to select what account chart template use this'
                ' company.'))
        if self.type in ['out_invoice', 'out_refund']:
            tipo_factura = 'F1'
            # TODO Los 5 tipos de facturas rectificativas
            if self.type == 'out_refund':
                tipo_factura = 'R4'
            tipo_desglose = self._get_sii_out_taxes()
            key = self.registration_key.code
            invoices = {
                "IDFactura": {
                    "IDEmisorFactura": {
                        "NIF": company.vat[2:]
                    },
                    "NumSerieFacturaEmisor": self.number[0:60],
                    "FechaExpedicionFacturaEmisor": invoice_date},
                "PeriodoImpositivo": {
                    "Ejercicio": ejercicio,
                    "Periodo": periodo
                },
                "FacturaExpedida": {
                    "TipoFactura": tipo_factura,
                    "ClaveRegimenEspecialOTrascendencia": key,
                    "DescripcionOperacion": self.sii_description[0:500],
                    "Contraparte": {
                        "NombreRazon": self.partner_id.name[0:120],
                        "NIF": self.partner_id.vat[2:]
                    },
                    "TipoDesglose": tipo_desglose
                }
            }
            if self.type == 'out_refund':
                invoices['FacturaExpedida'][
                    'TipoRectificativa'] = self.refund_type

                if self.refund_type == 'S':
                    base_rectificada = 0
                    cuota_rectificada = 0
                    for s in self.origin_invoices_ids:
                        base_rectificada += s.amount_untaxed
                        cuota_rectificada += s.amount_tax
                    invoices['FacturaExpedida']['ImporteRectificacion'] = {
                        'BaseRectificada': base_rectificada,
                        'CuotaRectificada': cuota_rectificada
                    }

        if self.type in ['in_invoice', 'in_refund']:
            # TODO Los 5 tipos de facturas rectificativas
            tipo_facturea = 'F1'
            if self.type == 'in_refund':
                tipo_facturea = 'R4'
            desglose_factura = self._get_sii_in_taxes()
            invoices = {
                "IDFactura": {
                    "IDEmisorFactura": {
                        "NIF": self.partner_id.vat[2:]
                    },
                    "NumSerieFacturaEmisor": self.supplier_invoice_number[
                        0:60],
                    "FechaExpedicionFacturaEmisor": invoice_date},
                "PeriodoImpositivo": {
                    "Ejercicio": ejercicio,
                    "Periodo": periodo
                },
                "FacturaRecibida": {
                    "TipoFactura": tipo_facturea,
                    "ClaveRegimenEspecialOTrascendencia": "01",
                    "DescripcionOperacion": self.sii_description[0:500],
                    "DesgloseFactura": desglose_factura,
                    "Contraparte": {
                        "NombreRazon": self.partner_id.name[0:120],
                        "NIF": self.partner_id.vat[2:]
                    },
                    "FechaRegContable": invoice_date,
                    "CuotaDeducible": self.amount_tax
                }
            }
            if self.type == 'in_refund':
                invoices['FacturaRecibida'][
                    'TipoRectificativa'] = self.refund_type

                if self.refund_type == 'S':
                    base_rectificada = 0
                    cuota_rectificada = 0
                    for s in self.origin_invoices_ids:
                        base_rectificada += s.amount_untaxed
                        cuota_rectificada += s.amount_tax
                    invoices['FacturaRecibida']['ImporteRectificacion'] = {
                        'BaseRectificada': base_rectificada,
                        'CuotaRectificada': cuota_rectificada
                    }

        return invoices

    @api.multi
    def _connect_sii(self, wsdl):
        today = fields.Date.today()
        sii_config = self.env['l10n.es.aeat.sii'].search([
            ('company_id', '=', self.company_id.id),
            ('public_key', '!=', False),
            ('private_key', '!=', False),
            '|', ('date_start', '=', False),
            ('date_start', '<=', today),
            '|', ('date_end', '=', False),
            ('date_end', '>=', today),
            ('state', '=', 'active')
        ], limit=1)
        if sii_config:
            public_crt = sii_config.public_key
            private_key = sii_config.private_key
        else:
            public_crt = self.env['ir.config_parameter'].get_param(
                'l10n_es_aeat_sii.publicCrt', False)
            private_key = self.env['ir.config_parameter'].get_param(
                'l10n_es_aeat_sii.privateKey', False)

        session = Session()
        session.cert = (public_crt, private_key)
        transport = Transport(session=session)

        history = HistoryPlugin()
        client = Client(wsdl=wsdl, transport=transport, plugins=[history])
        return client

    @api.multi
    def _send_invoice_to_sii(self):
        for invoice in self:
            company = invoice.company_id
            port_name = ''
            if invoice.type in ['out_invoice', 'out_refund']:
                wsdl = self.env['ir.config_parameter'].get_param(
                    'l10n_es_aeat_sii.wsdl_out', False)
                client = self._connect_sii(wsdl)
                port_name = 'SuministroFactEmitidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            elif invoice.type in ['in_invoice', 'in_refund']:
                wsdl = self.env['ir.config_parameter'].get_param(
                    'l10n_es_aeat_sii.wsdl_in', False)
                client = self._connect_sii(wsdl)
                port_name = 'SuministroFactRecibidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            serv = client.bind('siiService', port_name)
            if not invoice.sii_sent:
                tipo_comunicacion = 'A0'
            else:
                tipo_comunicacion = 'A1'
            header = invoice._get_header(tipo_comunicacion)
            invoices = invoice._get_invoices()
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
            else:
                queue_obj = self.env['queue.job']
                for invoice in self:
                    eta = invoice.company_id._get_sii_eta()
                    session = ConnectorSession.from_env(self.env)
                    new_delay = confirm_one_invoice.delay(
                        session, 'account.invoice', invoice.id, eta=eta)
                    queue_ids = queue_obj.search([
                        ('uuid', '=', new_delay)
                    ], limit=1)
                    invoice.invoice_jobs_ids |= queue_ids
        return res

    @api.multi
    def action_cancel(self):
        for queue in self.invoice_jobs_ids:
            if queue.state == 'started':
                raise Warning(_(
                    'You can not cancel this invoice because'
                    ' there is a job running!'))
            elif queue.state in ('pending', 'enqueued', 'failed'):
                queue.write({
                    'state': 'done',
                    'date_done': date.today()})
        return super(AccountInvoice, self).action_cancel()


@job(default_channel='root.invoice_validate_sii')
def confirm_one_invoice(session, model_name, invoice_id):
    model = session.env[model_name]
    invoice = model.browse(invoice_id)

    invoice._send_invoice_to_sii()
    session.cr.commit()
