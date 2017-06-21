# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Studio73 - Pablo Fuentes <pablo@studio73>
# Copyright 2017 Studio73 - Jordi Tolsà <jordi@studio73.es>
# Copyright 2017 Alberto Martín Cortada <alberto.martin@guadaltech.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from datetime import date,datetime
from requests import Session

from openerp.osv import osv, fields
from openerp import exceptions
from openerp.modules.registry import RegistryManager

_logger = logging.getLogger(__name__)

try:
    from zeep import Client
    from zeep.transports import Transport
    from zeep.plugins import HistoryPlugin
except (ImportError, IOError) as err:
    _logger.debug(err)


class AccountInvoice(osv.Model):
    _inherit = 'account.invoice'

    def _default_refund_type(self, cr, uid, data, context=None):
        if context is None:
            context = {}
        inv_type = context.get('type')
        return 'S' if inv_type in ['out_refund', 'in_refund'] else False

    def _default_registration_key(self, cr, uid, data, context=None):
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
        'registration_key': _default_registration_key,
        'refund_type': _default_refund_type,
        'sii_description': '/',
    }

    def copy(self, cr, uid, id, default, context={}):

        default['sii_sent'] = False
        default['sii_return'] = None
        default['sii_csv'] = None

        return super(AccountInvoice, self).copy(cr, uid, id, default, context=context)

    def onchange_refund_type_l10n_es_aeat_sii(self, cr, uid, ids, refund_type):
        for invoice in self.browse(cr, uid, ids):
            if refund_type == 'S' and not invoice.origin_invoices_ids:
                return {'warning':
                            {'message': 'You must have at least one refunded invoice'},
                        'values': {
                            'refund_type':None,
                        }
                        }

    def onchange_fiscal_position_l10n_es_aeat_sii(self, cr, uid, ids, fiscal_position):
        for invoice in self.browse(cr, uid, ids):
            if 'out' in invoice.type:
                key = invoice.fiscal_position.sii_registration_key_sale
            else:
                key = invoice.fiscal_position.sii_registration_key_purchase
            return {
                    'values': {
                        'registration_key': key or key.id,
                    }
            }

    def map_sii_tax_template(self, cr, uid, tax_template, mapping_taxes, invoice):
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

    def _get_sii_taxes_map(self, cr, uid, codes, date, invoice):
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
                tax = self.map_sii_tax_template(cr, uid, tax_template, mapping_taxes, invoice)
                if tax:
                    taxes.append(tax)
        return self.pool["account.tax"].browse(cr, uid, taxes)

    def _change_date_format(self, cr, uid, date):
        datetimeobject = datetime.strptime(date, '%Y-%m-%d')
        new_date = datetimeobject.strftime('%d-%m-%Y')
        return new_date

    def _get_sii_header(self, cr, uid, ids, company, tipo_comunicacion):

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


    def _get_sii_out_taxes(self, cr, uid, invoice):

        inv_line_obj = self.pool.get('account.invoice.line')

        taxes_dict = {}
        taxes_f = {}
        taxes_to = {}
        taxes_sfesb = self._get_sii_taxes_map(cr, uid,
                                          ['SFESB'], invoice.date_invoice, invoice)
        taxes_sfesbe = self._get_sii_taxes_map(cr, uid,
                                           ['SFESBE'], invoice.date_invoice, invoice)
        taxes_sfesisp = self._get_sii_taxes_map(cr, uid,
                                            ['SFESISP'], invoice.date_invoice, invoice)
        #         taxes_SFESISPS = self._get_taxes_map(cr, uid,
        #             ['SFESISPS'], invoice.date_invoice, invoice)
        taxes_sfens = self._get_sii_taxes_map(cr, uid,
                                          ['SFENS'], invoice.date_invoice, invoice)
        taxes_sfess = self._get_sii_taxes_map(cr, uid,
                                          ['SFESS'], invoice.date_invoice, invoice)
        taxes_sfesse = self._get_sii_taxes_map(cr, uid,
                                           ['SFESSE'], invoice.date_invoice, invoice)
        for inv_line in invoice.invoice_line:
            exempt_cause = self._get_sii_exempt_cause(cr, uid, inv_line.product_id, invoice)
            for tax_line in inv_line.invoice_line_tax_id:
                breakdown_taxes = (
                    taxes_sfesb + taxes_sfesisp + taxes_sfens + taxes_sfesb
                )
                if tax_line in breakdown_taxes:
                    tax_breakdown = taxes_dict.setdefault(
                        'DesgloseFactura', {},
                    )
                if tax_line in taxes_sfesb:
                    sub_dict = tax_breakdown.setdefault('Sujeta', {})
                    # TODO l10n_es no tiene impuesto exento de bienes
                    # corrientes nacionales
                    ex_taxes = (taxes_sfesbe + taxes_sfesbe + taxes_sfesisp)
                    if tax_line in ex_taxes:
                        sub_dict.setdefault('Exenta', {'BaseImponible': 0})
                        if exempt_cause:
                            sub_dict['Exenta']['CausaExencion'] = exempt_cause
                        sub_dict['Exenta']['BaseImponible'] += (
                            inv_line.price_subtotal
                        )
                    tax_breakdown['Sujeta'].setdefault('NoExenta', {
                        'TipoNoExenta': (
                            'S2' if tax_line in taxes_sfesisp else 'S1'
                        ),
                        'DesgloseIVA': {
                            'DetalleIVA': [],
                        },
                    })
                    inv_line_obj._update_sii_tax_line(cr,uid, inv_line, taxes_f, tax_line)
                # No sujetas
                if tax_line in taxes_sfens:
                    # FIXME: decidir que tipo se selecciona
                    t_nsub = 'ImportePorArticulos7_14_Otros'
                    nsub_dict = tax_breakdown.setdefault(
                        'NoSujeta', {t_nsub: 0},
                    )
                    nsub_dict[t_nsub] += inv_line.price_subtotal
                if tax_line in (taxes_sfess + taxes_sfesse):
                    type_breakdown = taxes_dict.setdefault(
                        'DesgloseTipoOperacion', {
                            'PrestacionServicios': {'Sujeta': {}},
                        },
                    )
                    service_dict = type_breakdown['PrestacionServicios']
                    if tax_line in taxes_sfesse:
                        exempt_dict = service_dict['Sujeta'].setdefault(
                            'Exenta', {'BaseImponible': 0},
                        )
                        if exempt_cause:
                            exempt_dict['CausaExencion'] = exempt_cause
                        exempt_dict['BaseImponible'] += inv_line.price_subtotal
                    # TODO Facturas no sujetas
                    if tax_line in taxes_sfess:
                        # TODO l10n_es_ no tiene impuesto ISP de servicios
                        # if tax_line in taxes_sfesisps:
                        #     TipoNoExenta = 'S2'
                        # else:
                        service_dict['Sujeta'].setdefault(
                            'NoExenta', {
                                'TipoNoExenta': 'S1',
                                'DesgloseIVA': {
                                    'DetalleIVA': [],
                                },
                            },
                        )
                        inv_line_obj._update_sii_tax_line(cr, uid, inv_line, taxes_to, tax_line)
        for val in taxes_f.values():
            val['CuotaRepercutida'] = round(val['CuotaRepercutida'], 2)
        if taxes_f:
            tax_breakdown['Sujeta']['NoExenta']['DesgloseIVA'][
                'DetalleIVA'] = taxes_f.values()
        if taxes_to:
            type_breakdown['PrestacionServicios']['Sujeta']['NoExenta'][
                'DesgloseIVA']['DetalleIVA'] = taxes_to.values()
        # Ajustes finales breakdown
        # - DesgloseFactura y DesgloseTipoOperacion son excluyentes
        # - Ciertos condicionantes obligan DesgloseTipoOperacion
        if ('DesgloseTipoOperacion' in taxes_dict
            and 'DesgloseFactura' in taxes_dict) or \
                ('DesgloseFactura' in taxes_dict
                 and self._get_sii_gen_type(cr, uid, invoice) in (2, 3)):
            taxes_dict.setdefault('DesgloseTipoOperacion', {})
            taxes_dict['DesgloseTipoOperacion']['Entrega'] = \
                taxes_dict['DesgloseFactura']
            del taxes_dict['DesgloseFactura']
        return taxes_dict

    def _get_sii_in_taxes(self, cr, uid, invoice):

        inv_line_obj = self.pool.get('account.invoice.line')

        taxes_dict = {}
        taxes_f = {}
        taxes_isp = {}
        taxes_sfrs = self._get_sii_taxes_map(cr, uid,
                                         ['SFRS'], invoice.date_invoice, invoice)
        taxes_sfrisp = self._get_sii_taxes_map(cr, uid,
                                           ['SFRISP'], invoice.date_invoice, invoice)
        for inv_line in invoice.invoice_line:
            for tax_line in inv_line.invoice_line_tax_id:
                if tax_line in taxes_sfrisp:
                    inv_line_obj._update_sii_tax_line(cr, uid, inv_line, taxes_isp, tax_line)
                elif tax_line in taxes_sfrs:
                    inv_line_obj._update_sii_tax_line(cr, uid, inv_line, taxes_f, tax_line)
        if taxes_isp:
            taxes_dict.setdefault(
                'InversionSujetoPasivo', {'DetalleIVA': taxes_isp.values()},
            )
        if taxes_f:
            taxes_dict.setdefault(
                'DesgloseIVA', {'DetalleIVA': [taxes_f.values()]},
            )
        return taxes_dict

    def _get_sii_invoice_dict(self, cr, uid, invoice):
        invoice_date = self._change_date_format(cr, uid, invoice.date_invoice)
        company = invoice.company_id
        ejercicio = invoice.period_id.fiscalyear_id.date_start[0:4]
        periodo = invoice.period_id.date_start[5:7]

        if not company.chart_template_id:
            raise exceptions.Warning(_(
                'You have to select what account chart template use this'
                ' company.'))
        inv_dict = {}
        if invoice.type in ['out_invoice', 'out_refund']:
            inv_dict = {
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
                    # TODO: Incluir los 5 tipos de facturas rectificativas
                    "TipoFactura": (
                        'R4' if invoice.type == 'out_refund' else 'F1'
                    ),
                    "ClaveRegimenEspecialOTrascendencia": (
                        invoice.registration_key.code
                    ),
                    "DescripcionOperacion": invoice.sii_description[0:500],
                    "Contraparte": {
                        "NombreRazon": invoice.partner_id.name[0:120],
                        "NIF": invoice.partner_id.vat[2:]
                    },
                    "TipoDesglose": self._get_sii_out_taxes(cr, uid ,invoice),
                    "ImporteTotal": invoice.amount_total
                }
            }
            exp_dict = inv_dict['FacturaExpedida']
            # Uso condicional de IDOtro/NIF
            exp_dict['Contraparte'].update(self._get_sii_identifier(cr, uid, invoice))

            if invoice.type == 'out_refund':
                exp_dict['TipoRectificativa'] = invoice.refund_type
                if invoice.refund_type == 'S':
                    base_rectificada = 0
                    cuota_rectificada = 0
                    for s in invoice.origin_invoices_ids:
                        base_rectificada += s.amount_untaxed
                        cuota_rectificada += s.amount_tax
                    exp_dict['ImporteRectificacion'] = {
                            'BaseRectificada': base_rectificada,
                            'CuotaRectificada': cuota_rectificada
                      }

        if invoice.type in ['in_invoice', 'in_refund']:
            inv_dict = {
                "IDFactura": {
                    "IDEmisorFactura": {},
                    "NumSerieFacturaEmisor": invoice.reference[0:60],
                    "FechaExpedicionFacturaEmisor": invoice_date},
                "PeriodoImpositivo": {
                    "Ejercicio": ejercicio,
                    "Periodo": periodo
                },
                "FacturaRecibida": {
                    # TODO: Incluir los 5 tipos de facturas rectificativas
                    "TipoFactura": (
                        'R4' if invoice.type == 'in_refund' else 'F1'
                    ),
                    "ClaveRegimenEspecialOTrascendencia": (
                        invoice.registration_key.code
                    ),
                    "DescripcionOperacion": invoice.sii_description[0:500],
                    "DesgloseFactura": self._get_sii_in_taxes(cr, uid, invoice),
                    "Contraparte": {
                        "NombreRazon": invoice.partner_id.name[0:120],
                    },
                    "FechaRegContable": invoice_date,
                    "ImporteTotal": invoice.amount_total,
                    "CuotaDeducible": invoice.amount_tax,
                }
            }

            # Uso condicional de IDOtro/NIF
            ident = self._get_sii_identifier(cr, uid, invoice)
            inv_dict['IDFactura']['IDEmisorFactura'].update(ident)
            inv_dict['FacturaRecibida']['Contraparte'].update(ident)
            if invoice.type == 'in_refund':
                rec_dict = inv_dict['FacturaRecibida']
                rec_dict['TipoRectificativa'] =  invoice.refund_type
                if invoice.refund_type == 'S':
                    base_rectificada = 0
                    cuota_rectificada = 0
                    for s in invoice.origin_invoices_ids:
                        base_rectificada += s.amount_untaxed
                        cuota_rectificada += s.amount_tax
                    rec_dict['ImporteRectificacion'] = {
                        'BaseRectificada': base_rectificada,
                        'CuotaRectificada': cuota_rectificada
                    }
        return inv_dict

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
            header = self._get_sii_header(cr, uid, invoice.id, company, tipo_comunicacion)
            inv_dict = self._get_sii_invoice_dict(cr, uid, invoice)
            try:
                if invoice.type in ['out_invoice', 'out_refund']:
                    res = serv.SuministroLRFacturasEmitidas(
                        header, inv_dict)
                elif invoice.type in ['in_invoice', 'in_refund']:
                    res = serv.SuministroLRFacturasRecibidas(
                        header, inv_dict)
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

    def _get_sii_gen_type(self, cr, uid, invoice):
        """Make a choice for general invoice type

        Returns:
            int: 1 (National), 2 (Intracom), 3 (Export)
        """
        if invoice.fiscal_position.name == u'Régimen Intracomunitario':
            return 2
        elif invoice.fiscal_position.name == u'Régimen Extracomunitario / Canarias, Ceuta y Melilla':
            return 3
        else:
            return 1

    def _get_sii_identifier(self, cr, uid, invoice):
        """Get the SII structure for a partner identifier depending on the
        conditions of the invoice.
        """
        gen_type = self._get_sii_gen_type(cr, uid, invoice)
        # Limpiar alfanum
        vat = ''.join(e for e in invoice.partner_id.vat if e.isalnum()).upper()
        if gen_type == 1 or vat.startswith('ES'):
            return {"NIF": vat[2:]}
        elif gen_type == 2:
            return {
                "IDOtro": {
                    "IDType": '02',
                    "ID": vat,
                }
            }
        elif gen_type == 3:
            return {
                "IDOtro": {
                    "CodigoPais": self.partner_id.country_id.code or vat[:2],
                    "IDType": '04',
                    "ID": vat,
                },
            }

    def _get_sii_exempt_cause(self, cr, uid, product, invoice):
        """Código de la causa de exención según 3.6 y 3.7 de la FAQ del SII."""
        gen_type = self._get_sii_gen_type(cr, uid, invoice)
        if gen_type == 2:
            return 'E5'
        elif gen_type == 3:
            return 'E2'
        elif product.sii_exempt_cause != 'none':
            return product.sii_exempt_cause

    def is_sii_invoice(self, cr, uid, invoice):
        """Hook method to be overridden in additional modules to verify
        if the invoice must be sended trough SII system, for special cases.

        :param self: Single invoice record
        :return: bool value indicating if the invoice should be sent to SII.
        """
        return True


class AccountInvoiceLine(osv.Model):
    _inherit = 'account.invoice.line'

    def _get_sii_line_price_subtotal(self, cr, uid, line):
        """Obtain the effective invoice line price after discount."""
        return line.price_unit * (1 - (line.discount or 0.0) / 100.0)

    def _get_sii_tax_line_req(self, cr, uid, line):
        """Get any possible tax amounts for 'Recargo equivalencia'."""
        invoice_obj = self.pool.get("account.invoice")
        invoice = line.invoice_id
        taxes_re = invoice_obj._get_sii_taxes_map(cr, uid,
                           ['RE'], invoice.date_invoice, invoice)
        for tax in line.invoice_line_tax_id:
            if tax in taxes_re:
                price = self._get_sii_line_price_subtotal(cr, uid ,line)
                taxes = tax.compute_all(
                    price, line.quantity, line.product_id,
                    line.invoice_id.partner_id,
                )
                taxes['percentage'] = tax.amount
                return taxes
        return {}

    def _update_sii_tax_line(self, cr, uid, line, tax_dict, tax_line):
        """Update the SII taxes dictionary for the passed tax line.

        :param self: Single invoice line record.
        :param tax_dict: Previous SII taxes dictionary.
        :param tax_line: Tax line that is being analyzed.
        """
        tax_type = str(tax_line.amount * 100)
        if tax_type not in tax_dict:
            tax_dict[tax_type] = {
                'TipoImpositivo': tax_type,
                'BaseImponible': 0,
                'CuotaRepercutida': 0,
                'CuotaSoportada': 0,
            }
        # Recargo de equivalencia
        tax_line_req = self._get_sii_tax_line_req(cr, uid, line)
        if tax_line_req:
            tipo_recargo = tax_line_req['percentage'] * 100
            cuota_recargo = tax_line_req['taxes'][0]['amount']
            tax_dict[tax_type]['TipoRecargoEquivalencia'] = tipo_recargo
            tax_dict[tax_type].setdefault('CuotaRecargoEquivalencia', 0)
            tax_dict[tax_type]['CuotaRecargoEquivalencia'] += cuota_recargo
        # Rest of the taxes
        taxes = self.pool.get('account.tax').compute_all(cr, uid, [tax_line],
            self._get_sii_line_price_subtotal(cr, uid, line), line.quantity,
            line.product_id, line.invoice_id.partner_id,
        )
        tax_dict[tax_type]['BaseImponible'] += taxes['total']
        if line.invoice_id.type in ['out_invoice', 'out_refund']:
            key = 'CuotaRepercutida'
        else:
            key = 'CuotaSoportada'
        tax_dict[tax_type][key] += taxes['taxes'][0]['amount']