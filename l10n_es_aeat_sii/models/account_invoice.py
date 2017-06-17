# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Studio73 - Pablo Fuentes <pablo@studio73>
# Copyright 2017 Studio73 - Jordi Tolsà <jordi@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from datetime import datetime, date
from requests import Session

from openerp import _, api, exceptions, fields, models
from openerp.modules.registry import RegistryManager

_logger = logging.getLogger(__name__)

try:
    from zeep import Client
    from zeep.transports import Transport
    from zeep.plugins import HistoryPlugin
except (ImportError, IOError) as err:
    _logger.debug(err)

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
        type = self.env.context.get('type')
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
    sii_send_error = fields.Text(string='SII Send Error')
    refund_type = fields.Selection(
        selection=[('S', 'By substitution'), ('I', 'By differences')],
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
            return {
                'warning':
                    {'message': 'Debes tener al menos una factura '
                     'vinculada que sustituir'}
            }

    @api.onchange('fiscal_position')
    def onchange_fiscal_position(self):
        for invoice in self:
            if invoice.fiscal_position:
                invoice.registration_key = \
                    invoice.fiscal_position.sii_registration_key

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
            raise exceptions.Warning(_(
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
    def _get_line_price_subtotal(self, line):
        self.ensure_one()
        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        return price

    @api.multi
    def _get_tax_line_req(self, tax_type, line, line_taxes):
        self.ensure_one()
        taxes = False
        taxes_re = self._get_taxes_map(
            ['RE'], line.invoice_id.date)
        if len(line_taxes) > 1:
            for tax in line_taxes:
                if tax in taxes_re:
                    price = self._get_line_price_subtotal(line)
                    taxes = tax.compute_all(
                        price, line.quantity, line.invoice_id.currency_id,
                        line.product_id, line.invoice_id.partner_id)
                    taxes['percentage'] = tax.amount
                    return taxes
        return taxes

    @api.multi
    def _get_sii_tax_line(self, tax_line, line, line_taxes, currency):
        self.ensure_one()
        tax_type = tax_line.amount
        tax_line_req = self._get_tax_line_req(tax_type, line, line_taxes)
        taxes = tax_line.compute_all(
            self._get_line_price_subtotal(line), line.invoice_id.currency_id,
            line.quantity, line.product_id, line.invoice_id.partner_id,
        )
        tax_sii = {
            "TipoImpositivo": tax_type,
            "BaseImponible": currency.compute(
                taxes['total_excluded'], self.company_id.currency_id,
            )
        }
        if tax_line_req:
            tipo_recargo = tax_line_req['percentage'] * 100
            cuota_recargo = tax_line_req['taxes'][0]['amount']
            tax_sii['TipoRecargoEquivalencia'] = tipo_recargo
            tax_sii['CuotaRecargoEquivalencia'] = currency.compute(
                cuota_recargo, self.company_id.currency_id,
            )
        if self.type in ['out_invoice', 'out_refund']:
            tax_sii['CuotaRepercutida'] = currency.compute(
                taxes['taxes'][0]['amount'], self.company_id.currency_id,
            )
        if self.type in ['in_invoice', 'in_refund']:
            tax_sii['CuotaSoportada'] = currency.compute(
                taxes['taxes'][0]['amount'], self.company_id.currency_id,
            )
        return tax_sii

    @api.multi
    def _update_sii_tax_line(self, tax_sii, tax_line, line, line_taxes, currency):
        self.ensure_one()
        tax_type = tax_line.amount
        tax_line_req = self._get_tax_line_req(tax_type, line, line_taxes)
        taxes = tax_line.compute_all(
            self._get_line_price_subtotal(line),
            line.invoice_id.currency_id, line.quantity, line.product_id, line.invoice_id.partner_id)
        if tax_line_req:
            tipo_recargo = tax_line_req['percentage'] * 100
            cuota_recargo = tax_line_req['taxes'][0]['amount']
            tax_sii[str(tax_type)]['TipoRecargoEquivalencia'] += tipo_recargo
            tax_sii[str(tax_type)]['CuotaRecargoEquivalencia'] += currency.compute(cuota_recargo,
                                                                                   self.company_id.currency_id)

        tax_sii[str(tax_type)]['BaseImponible'] += currency.compute(taxes['total_excluded'],
                                                                    self.company_id.currency_id)
        if self.type in ['out_invoice', 'out_refund']:
            tax_sii[str(tax_type)]['CuotaRepercutida'] += currency.compute(taxes['taxes'][0]['amount'],
                                                                           self.company_id.currency_id)
        if self.type in ['in_invoice', 'in_refund']:
            tax_sii[str(tax_type)]['CuotaSoportada'] += currency.compute(taxes['taxes'][0]['amount'],
                                                                         self.company_id.currency_id)
        return tax_sii

    @api.multi
    def _get_sii_out_taxes(self, currency):
        self.ensure_one()
        taxes_sii = {}
        taxes_f = {}
        taxes_to = {}

        taxes_sfesb = self._get_taxes_map(['SFESB'], self.date)
        taxes_sfesbe = self._get_taxes_map(['SFESBE'], self.date)
        taxes_sfesisp = self._get_taxes_map(['SFESISP'], self.date)
        # taxes_sfesisps = self._get_taxes_map(['SFESISPS'], self.date_invoice)
        taxes_sfens = self._get_taxes_map(['SFENS'], self.date)
        taxes_sfess = self._get_taxes_map(['SFESS'], self.date)
        taxes_sfesse = self._get_taxes_map(['SFESSE'], self.date)
        for line in self.invoice_line_ids:
            for tax_line in line.invoice_line_tax_ids:
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
                                    'BaseImponible': currency.compute(
                                        line.price_subtotal,
                                        self.company_id.currency_id)}

                                if line.product_id.sii_exempt_cause != 'none':
                                    inv_breakdown['Sujeta']['Exenta'].update({
                                        'CausaExencion':line.product_id.sii_exempt_cause})
                            else:
                                inv_breakdown['Sujeta']['Exenta'][
                                    'BaseImponible'] += currency.compute(line.price_subtotal,
                                                                         self.company_id.currency_id)

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
                            tax_type = tax_line.amount
                            if str(tax_type) not in taxes_f:
                                taxes_f[str(tax_type)] = \
                                    self._get_sii_tax_line(
                                        tax_line, line,
                                        line.invoice_line_tax_ids, currency)
                            else:
                                taxes_f = self._update_sii_tax_line(
                                    taxes_f, tax_line, line,
                                    line.invoice_line_tax_ids, currency)
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
                                    'BaseImponible': currency.compute(line.price_subtotal,
                                                                      self.company_id.currency_id)
                                    }
                            if line.product_id.sii_exempt_cause != 'none':
                                taxes_sii['DesgloseTipoOperacion'][
                                    'PrestacionServicios']['Sujeta']['Exenta'].update({
                                        'CausaExencion': line.product_id.sii_exempt_cause})
                         else:
                             taxes_sii['DesgloseTipoOperacion'][
                                 'PrestacionServicios']['Sujeta']['Exenta'][
                                     'BaseImponible'] += currency.compute(line.price_subtotal,
                                                                          self.company_id.currency_id)
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
                            tax_type = tax_line.amount
                            if str(tax_type) not in taxes_to:
                                taxes_to[str(tax_type)] = \
                                    self._get_sii_tax_line(
                                        tax_line, line,
                                        line.invoice_line_tax_ids, currency)
                            else:
                                taxes_to = self._update_sii_tax_line(
                                    taxes_to, tax_line, line,
                                    line.invoice_line_tax_ids, currency)
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
    def _get_sii_in_taxes(self, currency):
        self.ensure_one()
        taxes_sii = {}
        taxes_f = {}
        taxes_isp = {}

        taxes_sfrs = self._get_taxes_map(['SFRS'], self.date)
        taxes_sfrisp = self._get_taxes_map(['SFRISP'], self.date)
        for line in self.invoice_line_ids:
            for tax_line in line.invoice_line_tax_ids:
                if tax_line in taxes_sfrs or tax_line in taxes_sfrisp:
                    if tax_line in taxes_sfrisp:
                        if 'InversionSujetoPasivo' not in taxes_sii:
                            taxes_sii['InversionSujetoPasivo'] = {}
                            taxes_sii['InversionSujetoPasivo'][
                                'DetalleIVA'] = []
                        tax_type = tax_line.amount
                        if str(tax_type) not in taxes_isp:
                            taxes_isp[str(tax_type)] = self._get_sii_tax_line(
                                tax_line, line, line.invoice_line_tax_ids, currency)
                        else:
                            taxes_isp = self._update_sii_tax_line(
                                taxes_isp, tax_line, line,
                                line.invoice_line_tax_ids, currency)
                    else:
                        if 'DesgloseIVA' not in taxes_sii:
                            taxes_sii['DesgloseIVA'] = {}
                            taxes_sii['DesgloseIVA'][
                                'DetalleIVA'] = []
                        tax_type = tax_line.amount
                        if str(tax_type) not in taxes_f:
                            taxes_f[str(tax_type)] = self._get_sii_tax_line(
                                tax_line, line, line.invoice_line_tax_ids, currency)
                        else:
                            taxes_f = self._update_sii_tax_line(
                                taxes_f, tax_line, line,
                                line.invoice_line_tax_ids, currency)
        for key, line in taxes_f.iteritems():
            taxes_sii['DesgloseIVA']['DetalleIVA'].append(line)
        for key, line in taxes_isp.iteritems():
            taxes_sii['InversionSujetoPasivo']['DetalleIVA'].append(line)
        return taxes_sii

    @api.multi
    def _get_invoices(self):
        self.ensure_one()
        if not self.partner_id.vat:
            raise exceptions.Warning(_(
                "The partner has not a VAT configured."))
        invoice_date = self._change_date_format(self.date)
        company = self.company_id
        currency = self.currency_id.with_context(date=invoice_date or fields.Date.context_today(self))
        ejercicio = fields.Date.from_string(
            self.date).year
        periodo = '%02d' % fields.Date.from_string(
            self.date).month
        if not company.chart_template_id:
            raise exceptions.Warning(_(
                'You have to select what account chart template use this'
                ' company.'))
        if self.type in ['out_invoice', 'out_refund']:
            tipo_factura = 'F1'
            # TODO Los 5 tipos de facturas rectificativas
            if self.type == 'out_refund':
                tipo_factura = 'R4'
            tipo_desglose = self._get_sii_out_taxes(currency)
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
                    },
                    "TipoDesglose": tipo_desglose,
                    "ImporteTotal": self.amount_total
                }
            }
            # Uso condicional de IDOtro/NIF
            invoices['FacturaExpedida']['Contraparte'].update(
                self._get_sii_identifier())
            if self.type == 'out_refund':
                invoices['FacturaExpedida'][
                    'TipoRectificativa'] = self.refund_type

                if self.refund_type == 'S':
                    base_rectificada = 0
                    cuota_rectificada = 0
                    for s in self.origin_invoices_ids:
                        base_rectificada += currency.compute(s.amount_untaxed,
                                                             self.company_id.currency_id)
                        cuota_rectificada += currency.compute(s.amount_tax,
                                                              self.company_id.currency_id)
                    invoices['FacturaExpedida']['ImporteRectificacion'] = {
                        'BaseRectificada': currency.compute(base_rectificada,
                                                            self.company_id.currency_id),
                        'CuotaRectificada': currency.compute(cuota_rectificada,
                                                             self.company_id.currency_id)
                    }

        if self.type in ['in_invoice', 'in_refund']:
            # TODO Los 5 tipos de facturas rectificativas
            tipo_facturea = 'F1'
            if self.type == 'in_refund':
                tipo_facturea = 'R4'
            desglose_factura = self._get_sii_in_taxes(currency)
            invoices = {
                "IDFactura": {
                    "IDEmisorFactura": {
                        "NIF": self.partner_id.vat[2:]
                    },
                    "NumSerieFacturaEmisor":
                        self.supplier_invoice_number and
                        self.supplier_invoice_number[0:60],
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
                    "CuotaDeducible": currency.compute(self.amount_tax,
                                                       self.company_id.currency_id)
                }
            }
            if self.type == 'in_refund':
                invoices['FacturaRecibida'][
                    'TipoRectificativa'] = self.refund_type

                if self.refund_type == 'S':
                    base_rectificada = 0
                    cuota_rectificada = 0
                    for s in self.origin_invoices_ids:
                        base_rectificada += currency.compute(s.amount_untaxed,
                                                             self.company_id.currency_id)
                        cuota_rectificada += currency.compute(s.amount_tax,
                                                              self.company_id.currency_id)
                    invoices['FacturaRecibida']['ImporteRectificacion'] = {
                        'BaseRectificada': currency.compute(base_rectificada,
                                                            self.company_id.currency_id),
                        'CuotaRectificada': currency.compute(cuota_rectificada,
                                                             self.company_id.currency_id)
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
        for invoice in self.filtered(lambda i: i.state in ['open', 'paid']):
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
            try:
                invoices = invoice._get_invoices()
            except Exception as fault:
                new_cr = RegistryManager.get(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                self.with_env(env).sii_send_error = fault
                new_cr.commit()
                new_cr.close()
                raise
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
                send_error = False
                res_line = res['RespuestaLinea'][0]
                if res_line['CodigoErrorRegistro']:
                    send_error = u"{} | {}".format(
                        unicode(res_line['CodigoErrorRegistro']),
                        unicode(res_line['DescripcionErrorRegistro'])[:60])
                self.sii_send_error = send_error
            except Exception as fault:
                self.sii_return = fault
                self.sii_send_error = fault

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        queue_obj = self.env['queue.job']
        for invoice in self:
            company = invoice.company_id
            if company.sii_enabled and company.sii_method == 'auto' and \
                    invoice.is_sii_invoice():
                if not company.use_connector:
                    invoice._send_invoice_to_sii()
                else:
                    eta = company._get_sii_eta()
                    session = ConnectorSession.from_env(self.env)
                    new_delay = confirm_one_invoice.delay(
                        session, 'account.invoice', invoice.id, eta=eta)
                    queue_ids = queue_obj.search([
                        ('uuid', '=', new_delay)
                    ], limit=1)
                    invoice.invoice_jobs_ids |= queue_ids
        return res

    @api.multi
    def send_sii(self):
        queue_obj = self.env['queue.job']
        for invoice in self:
            company = invoice.company_id
            if company.sii_enabled:
                if not company.use_connector:
                    invoice._send_invoice_to_sii()
                else:
                    eta = company._get_sii_eta()
                    session = ConnectorSession.from_env(self.env)
                    new_delay = confirm_one_invoice.delay(
                        session, 'account.invoice', invoice.id, eta=eta)
                    queue_ids = queue_obj.search([
                        ('uuid', '=', new_delay)
                    ], limit=1)
                    invoice.invoice_jobs_ids |= queue_ids

    @api.multi
    def action_cancel(self):
        for queue in self.invoice_jobs_ids:
            if queue.state == 'started':
                raise exceptions.Warning(_(
                    'You can not cancel this invoice because'
                    ' there is a job running!'))
            elif queue.state in ('pending', 'enqueued', 'failed'):
                queue.write({
                    'state': 'done',
                    'date_done': date.today()})
        return super(AccountInvoice, self).action_cancel()

    @api.one
    def copy(self, default=None):
        default = default or {}
        default.update({
            'sii_sent': False,
            'sii_csv': None,
            'sii_return': None
        })

        return super(AccountInvoice, self).copy(default)

    @api.multi
    def _get_sii_identifier(self):
        self.ensure_one()
        codPais = self.partner_id.vat[:2]
        dic_ret = {}
        if codPais != 'ES':
            if self.fiscal_position.name == u'Régimen Intracomunitario':
                idType = '02'
            else:
                idType = '04'
            dic_ret = {
                "IDOtro": {
                    "CodigoPais": codPais,
                    "IDType": idType,
                    "ID": self.partner_id.vat
                }
            }
        else:
            dic_ret = {"NIF": self.partner_id.vat[2:]}
        return dic_ret

    def is_sii_invoice(self):
        """ is_sii_invoice() -> bool
            Hook method to be overridden in additional modules to verify
            if the invoice must be sended trought SII system, for
            special cases.
            :param
            :return: bool
        """
        return True

@job(default_channel='root.invoice_validate_sii')
def confirm_one_invoice(session, model_name, invoice_id):
    model = session.env[model_name]
    invoice = model.browse(invoice_id)

    invoice._send_invoice_to_sii()
    session.cr.commit()
