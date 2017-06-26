# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp.osv import fields, osv
from requests import Session
from zeep import Client
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from datetime import datetime
from tools.translate import _
from openerp.exceptions import Warning


import logging
_logger = logging.getLogger(__name__)


class account_invoice(osv.Model):
    _inherit = 'account.invoice'

    def _default_refund_type(self, cr, uid, invoice_type, context=None):
        return 'S' if invoice_type in ('out_refund', 'in_refund') else False

    def _get_default_key(self, cr, uid, ids, context=None):
        sii_key_obj = self.pool.get('aeat.sii.mapping.registration.keys')
        type_invoice = self.browse(cr, uid, ids, context)
        type = type_invoice.type
        if type in ['in_invoice', 'in_refund']:
            key = sii_key_obj.search(cr, uid, [('code', '=', '01'), ('type', '=', 'purchase')], limit=1)
        else:
            key = sii_key_obj.search(cr, uid, [('code', '=', '01'), ('type', '=', 'sale')], limit=1)

        return key[0]


    _columns = {
        'sii_description': fields.text('SII Description', required=True),
        'sii_sent': fields.boolean('SII Sent'),
        'sii_csv': fields.char(string='SII CSV', size=128, readonly=True),
        'sii_return': fields.text('SII Return', readonly=True),
        'sii_send_error': fields.text('SII Send Error', readonly=True),
        'sii_refund_type': fields.selection([('S', 'By substitution'),('I', 'By differences')], 'Refund Type'),
        'sii_registration_key': fields.many2one('aeat.sii.mapping.registration.keys', "Registration key", required=True),
        'sii_enabled': fields.related('company_id', 'sii_enabled', type='boolean', relation='res.company', string='SII Enabled', store=True, readonly=True),
    }     

    _defaults = {
     'sii_registration_key' : _get_default_key,
     'sii_description': '/'
    }

    #TODO
    def onchange_refund_type(self, cr, uid):
        if self.sii_refund_type == 'S' and not self.origin_invoices_ids:
            self.sii_refund_type = False
            return {'warning':
                {'message': 'Debes tener al menos una factura '
                            'vinculada que sustituir'
                 }
            }
    #TODO
    def onchange_fiscal_position(self, cr, uid, invoice_id, context=None):
        invoice = self.browse(cr, uid, invoice_id)

        key = False
        if invoice.fiscal_position:
            if 'out' in invoice.type:
                key = invoice.fiscal_position.sii_registration_key_sale
            else:
                key = invoice.fiscal_position.sii_registration_key_purchase

        if key:
            self.write(cr, uid, invoice_id, {'sii_registration_key': key})

        return invoice

    def create(self, cr, uid, vals, context=None):
        invoice_id = super(account_invoice, self).create(cr, uid, vals, context)
        invoice = self.browse(cr, uid, invoice_id)
        if invoice.fiscal_position and not invoice.sii_registration_key:
            self.onchange_fiscal_position(cr, uid, invoice.id)

        return invoice

    def write(self, cr, uid, ids, vals, context=None):
        invoice = super(account_invoice, self).write(cr, uid, ids, vals, context)
        if vals.get('fiscal_position') and not vals.get('sii_registration_key'):
            _logger.debug("TODO write" )

        return invoice


    def map_tax_template(self, cr, uid, tax_template, mapping_taxes, invoice):
        # Adapted from account_chart_update module
        """Adds a tax template -> tax id to the mapping."""
        if not tax_template:
            return self.pool.get('account.tax')

        if mapping_taxes.get(tax_template):
            return mapping_taxes[tax_template]

        # search inactive taxes too, to avoid re-creating
        # taxes that have been deactivated before
        tax_obj = self.pool.get('account.tax')
        criteria = ['|',
                    ('name', '=', tax_template.name),
                    ('description', '=', tax_template.name)]
        if tax_template.description:
            criteria = ['|', '|'] + criteria
            criteria += [('description', '=', tax_template.description),
                         ('name', '=', tax_template.description)]
        criteria += [('company_id', '=', invoice.company_id.id)]
        tax_ids = tax_obj.search(cr, uid, criteria, limit=1)
        mapping_taxes[tax_template] = tax_ids and tax_ids[0] or False

        return mapping_taxes[tax_template]

    def _get_sii_taxes_map(self, cr, uid, codes, invoice):
        # Return the codes that correspond to that sii map line codes
        taxes = []
        sii_map_obj = self.pool.get('aeat.sii.map')
        sii_map_line_obj = self.pool.get('aeat.sii.map.lines')
        sii_map = sii_map_obj.browse(cr, uid, sii_map_obj.search(
            cr, uid,
            ['|', ('date_from', '<=', invoice.date_invoice), ('date_from', '=', False),
             '|', ('date_to', '>=', invoice.date_invoice), ('date_to', '=', False)], limit=1)[0])
        mapping_taxes = {}
        for code in codes:
            sii_map_line_id = sii_map_line_obj.search(cr, uid, [('code', '=', code),
                                                                ('sii_map_id', '=', sii_map.id)])
            if sii_map_line_id:
                tax_search_obj = sii_map_line_obj.browse(cr, uid, sii_map_line_id[0])
                tax_templates = tax_search_obj and tax_search_obj.taxes or []
                for tax_template in tax_templates:
                    tax = self.map_tax_template(cr, uid, tax_template, mapping_taxes, invoice)
                    if tax:
                        taxes.append(tax)
        _logger.debug("taxes %s" % taxes)
        return self.pool.get("account.tax").browse(cr, uid, taxes)

    def _change_date_format(self, cr, uid, date):
        date_time_object = datetime.strptime(date,'%Y-%m-%d')
        new_date = date_time_object.strftime('%d-%m-%Y')

        return new_date


    def _get_header(self, cr, uid, ids, company, comunication_type):
        if not company.partner_id.vat:
           raise Warning(_(
                "No VAT configured for the company '{}'").format(company.name))

        header = { "IDVersionSii": company.version_sii,
                   "Titular": {
                      "NombreRazon": company.name,
                      "NIF": company.vat[2:]},
                   "TipoComunicacion": comunication_type
        }

        return header
    
    def _get_sii_out_taxes(self, cr, uid, invoice):
        taxes_dict = {}
        taxes_f = {}
        taxes_to = {}
        taxes_sfesb = self._get_sii_taxes_map(cr, uid, ['SFESB'], invoice)
        taxes_sfesbe = self._get_sii_taxes_map(cr, uid, ['SFESBE'], invoice)
        taxes_sfesisp = self._get_sii_taxes_map(cr, uid, ['SFESISP'], invoice)
        #taxes_sfesisps = self._get_sii_taxes_map(cr, uid, ['SFESISPS'], invoice)
        taxes_sfens = self._get_sii_taxes_map(cr, uid, ['SFENS'], invoice)
        taxes_sfess = self._get_sii_taxes_map(cr, uid, ['SFESS'], invoice)
        taxes_sfesse = self._get_sii_taxes_map(cr, uid, ['SFESSE'], invoice)
        for line in invoice.invoice_line:
            exempt_cause = self._get_sii_exempt_cause(cr, uid, invoice, line.product_id.id)
            for tax_line in line.invoice_line_tax_id:
                breakdown_taxes = (
                    taxes_sfesb + taxes_sfesisp + taxes_sfens + taxes_sfesbe

                )
                if tax_line in breakdown_taxes:
                    tax_breakdown = taxes_dict.setdefault(
                        'DesgloseFactura', {},
                    )

                    if tax_line in (taxes_sfesb + taxes_sfesbe + taxes_sfesisp):
                        sub_dict = tax_breakdown.setdefault('Sujeta', {})

                        # TODO l10n_es no tiene impuesto exento de bienes
                        # corrientes nacionales
                        ex_taxes = taxes_sfesbe
                        if tax_line in ex_taxes:
                            sub_dict.setdefault('Exenta', {'BaseImponible': 0})
                            if exempt_cause:
                                sub_dict['Exenta']['CausaExencion'] = exempt_cause

                            sub_dict['Exenta']['BaseImponible'] += (
                                line.price_subtotal
                            )
                        else:
                            sub_dict.setdefault('NoExenta', {
                                'TipoNoExenta': (
                                    'S2' if tax_line in taxes_sfesisp else 'S1'
                                ),
                                'DesgloseIVA': {
                                    'DetalleIVA': [],
                                },
                            })
                        self.pool.get('account.invoice.line')._update_sii_tax_line(cr, uid, taxes_f, tax_line, line)

                    # No sujetas
                    if tax_line in taxes_sfens:
                        # FIXME: decidir que tipo se selecciona
                        t_nsub = 'ImportePorArticulos7_14_Otros'
                        nsub_dict = tax_breakdown.setdefault(
                            'NoSujeta', {t_nsub: 0},
                        )
                        nsub_dict[t_nsub] += line.price_subtotal
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
                        exempt_dict['BaseImponible'] += line.price_subtotal

                    # TODO Facturas No sujetas
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

                        self.pool.get('account.invoice.line')._update_sii_tax_line(cr, uid, taxes_to, tax_line, line)

        for val in taxes_f.values() + taxes_to.values():
            val['CuotaRepercutida'] = round(val['CuotaRepercutida'], 2)
            val['BaseImponible'] = round(val['BaseImponible'], 2)

        if taxes_f:
            breakdown = tax_breakdown['Sujeta']['NoExenta']['DesgloseIVA']
            breakdown['DetalleIVA'] = taxes_f.values()

        if taxes_to:
            sub = type_breakdown['PrestacionServicios']['Sujeta']
            sub['NoExenta']['DesgloseIVA']['DetalleIVA'] = taxes_to.values()
        # Ajustes finales breakdown
        # - DesgloseFactura y DesgloseTipoOperacion son excluyentes
        # - Ciertos condicionantes obligan DesgloseTipoOperacion
        if (('DesgloseTipoOperacion' in taxes_dict and
                    'DesgloseFactura' in taxes_dict) or \
                ('DesgloseFactura' in taxes_dict and
                         self._get_sii_gen_type(cr, uid, invoice) in (2, 3))):
            taxes_dict.setdefault('DesgloseTipoOperacion', {})
            taxes_dict['DesgloseTipoOperacion']['Entrega'] = \
                taxes_dict['DesgloseFactura']
            del taxes_dict['DesgloseFactura']

        return taxes_dict

    def _get_sii_in_taxes(self, cr, uid, invoice): 
        taxes_dict = {}
        taxes_f = {}
        taxes_isp = {}
        taxes_sfrs = self._get_sii_taxes_map(cr, uid, ['SFRS'], invoice)
        taxes_sfrisp = self._get_sii_taxes_map(cr, uid, ['SFRISP'], invoice)

        for line in invoice.invoice_line:
            for tax_line in line.invoice_line_tax_id:
                if tax_line in taxes_sfrisp:
                    self.pool.get('account.invoice.line')._update_sii_tax_line(cr, uid, taxes_isp, tax_line, line)
                elif tax_line in taxes_sfrs:
                    self.pool.get('account.invoice.line')._update_sii_tax_line(cr, uid, taxes_f, tax_line, line)

        if taxes_isp:
            taxes_dict.setdefault(
                'InversionSujetoPasivo', {'DetalleIVA': taxes_isp.values()},
            )

        if taxes_f:
            taxes_dict.setdefault(
                'DesgloseIVA', {'DetalleIVA': taxes_f.values()},
            )

        for val in taxes_isp.values() + taxes_f.values():
            val['CuotaSoportada'] = round(val['CuotaSoportada'], 2)
            val['BaseImponible'] = round(val['BaseImponible'], 2)
        return taxes_dict

    def _sii_check_exceptions(self, cr, uid, invoice_id):
        """Inheritable method for exceptions control when sending SII invoices.
        """
        invoice = self.browse(cr, uid, invoice_id)
        if not invoice.partner_id.vat:
            raise osv.except_osv(_('Warning!'),
                _("The partner has not a VAT configured.")
            )
        # if not invoice.company_id.chart_template_id:
        #     raise osv.except_osv(_('Warning!'),
        #         _('You have to select what account chart template use this company.'))
        if not invoice.company_id.sii_enabled:
            raise osv.except_osv(_('Warning!'),
                _("This company doesn't have SII enabled.")
            )
    
    def _get_sii_invoice_dict_out(self, cr, uid, invoice_id):
        invoice = self.browse(cr, uid, invoice_id)
        if not invoice.partner_id.vat:
            raise osv.except_osv(_('Warning!'),
                                 _("The partner %s has not a VAT configured." %invoice.partner_id.name))

        invoice_date = self._change_date_format(cr, uid, invoice.date_invoice)
        if invoice.period_id.fiscalyear_id.date_start[0:4] == invoice.period_id.fiscalyear_id.date_stop[0:4]:
            ejercicio = invoice.period_id.fiscalyear_id.date_start[0:4]
        else:
            ejercicio = invoice.period_id.date_start[0:4]

        periodo = invoice.period_id.date_start[5:7]

        inv_dict = {
            "IDFactura":{
                "IDEmisorFactura": {
                    "NIF": invoice.company_id.vat[2:]
                },
                "NumSerieFacturaEmisor": invoice.number,
                "FechaExpedicionFacturaEmisor": invoice_date
            },
            "PeriodoImpositivo": {
                "Ejercicio": ejercicio,
                "Periodo": periodo,
            },
            "FacturaExpedida": {
                # TODO: Incluir los 5 tipos de facturas rectificativas
                "TipoFactura": (
                    'R4' if invoice.type == 'out_refund' else 'F1'
                ),
                "ClaveRegimenEspecialOTrascendencia": (
                    invoice.sii_registration_key.code
                ),
                "DescripcionOperacion": invoice.sii_description[0:500],
                "Contraparte": {
                    "NombreRazon": invoice.partner_id.name[0:120],
                },
                "TipoDesglose": self._get_sii_out_taxes(cr, uid, invoice),
                "ImporteTotal": invoice.amount_total,
            }
        }

        exp_dict = inv_dict['FacturaExpedida']
        # Uso condicional de IDOtro/NIF
        #TODO
        exp_dict['Contraparte'].update(self._get_sii_identifier(cr, uid, invoice.id))
        if invoice.type == 'out_refund':
            exp_dict['TipoRectificativa'] = invoice.sii_refund_type
            if invoice.sii_refund_type == 'S':
                exp_dict['ImporteRectificacion'] = {
                    # TODO review
                    'BaseRectificada': invoice.amount_untaxed,
                    'CuotaRectificada': invoice.amount_tax,

                }
        return inv_dict

    def _get_sii_invoice_dict_in(self, cr, uid, invoice_id, context=None):
        invoice = self.browse(cr, uid, invoice_id)
        invoice_date = self._change_date_format(cr, uid, invoice.date_invoice)
        if invoice.period_id.fiscalyear_id.date_start[0:4] == invoice.period_id.fiscalyear_id.date_stop[0:4]:
            ejercicio = invoice.period_id.fiscalyear_id.date_start[0:4]
        else:
            ejercicio = invoice.period_id.date_start[0:4]

        periodo = invoice.period_id.date_start[5:7]

        inv_dict = {
            "IDFactura": {
                "IDEmisorFactura": {},
                "NumSerieFacturaEmisor": (
                    (invoice.supplier_invoice_number or '')[:60]
                ),
                "FechaExpedicionFacturaEmisor": invoice_date
            },
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
                    invoice.sii_registration_key.code
                ),
                "DescripcionOperacion": invoice.sii_description[0:500],
                "DesgloseFactura": self._get_sii_in_taxes(cr, uid, invoice),
                "Contraparte": {
                    "NombreRazon": invoice.partner_id.name[0:120],
                },
                "FechaRegContable": invoice_date,
                "ImporteTotal": invoice.amount_total,
                "CuotaDeducible": invoice.amount_tax
            }
        }

        ident = self._get_sii_identifier(cr, uid, invoice_id)
        inv_dict['IDFactura']['IDEmisorFactura'].update(ident)
        inv_dict['FacturaRecibida']['Contraparte'].update(ident)

        if invoice.type == 'in_refund':
            rec_dict = inv_dict['FacturaRecibida']
            rec_dict['TipoRectificativa'] = invoice.sii_refund_type
            if invoice.sii_refund_type == 'S':
                rec_dict['ImporteRectificacion'] = {
                    'BaseRectificada': invoice.amount_untaxed,
                    'CuotaRectificada': invoice.amount_tax,
                }

        return inv_dict

    def _get_sii_invoice_dict(self, cr, uid, invoice_id, context=None):
        self._sii_check_exceptions(cr, uid, invoice_id)
        invoice = self.browse(cr, uid, invoice_id)
        if invoice.type in ['out_invoice', 'out_refund']:
            return self._get_sii_invoice_dict_out(cr, uid, invoice_id)
        elif invoice.type in ['in_invoice', 'in_refund']:
            return self._get_sii_invoice_dict_in(cr, uid, invoice_id)

        return {}

    def _connect_sii(self, cr, uid, wsdl, company_id):
        today = datetime.now().date()
        sii_config_pool = self.pool.get('l10n.es.aeat.sii')
        sii_config_id = sii_config_pool.search(cr, uid,[
            ('company_id', '=', company_id),
            ('public_key', '!=', False),
            ('private_key', '!=', False),
            '|',
            ('date_start', '=', False),
            ('date_start', '<=', today),
            '|',
            ('date_end', '=', False),
            ('date_end', '>=', today),
            ('state', '=', 'active'),
        ], limit=1)

        if not sii_config_id:
            raise osv.except_osv(_('Error!'), _("There is no certificate configured for this company and date"))

        sii_config = sii_config_pool.browse(cr, uid, sii_config_id[0])

        publicCrt = sii_config.public_key
        privateKey = sii_config.private_key

        session = Session()
        session.cert = (publicCrt, privateKey)
        transport = Transport(session=session)
        history = HistoryPlugin()
        client = Client(wsdl=wsdl,transport=transport,plugins=[history])
        return client
    
    def _send_invoice_to_sii(self, cr, uid, ids):
        for invoice in self.browse(cr, uid, ids):
            company = invoice.company_id
            port_name = ''
            if invoice.type in['out_invoice','out_refund']:
                wsdl = company.wsdl_out
                port_name = 'SuministroFactEmitidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            elif invoice.type in ['in_invoice','in_refund']:
                wsdl = company.wsdl_in
                port_name = 'SuministroFactRecibidas'
                if company.sii_test:
                    port_name += 'Pruebas'

            client = self._connect_sii(cr, uid, wsdl, company.id)
            serv = client.bind('siiService', port_name)
            if not invoice.sii_sent:
                tipo_comunicacion = 'A0'
            else:
                tipo_comunicacion = 'A1'

            header = self._get_header(cr, uid, invoice.id, company, tipo_comunicacion)
            inv_dict = self._get_sii_invoice_dict(cr, uid, invoice.id)
            _logger.debug("header %s" %header)
            _logger.debug("inv_dict %s" %inv_dict)

            try:

                if invoice.type in ['out_invoice','out_refund']:
                    res = serv.SuministroLRFacturasEmitidas(header, inv_dict)
                elif invoice.type in ['in_invoice','in_refund']:
                    res = serv.SuministroLRFacturasRecibidas(header, inv_dict)
                # TODO Facturas intracomunitarias 66 RIVA
                # elif invoice.fiscal_position.id == self.env.ref(
                #     'account.fp_intra').id:
                #     res = serv.SuministroLRDetOperacionIntracomunitaria(
                #         header, invoices)
                res_line = res['RespuestaLinea'][0]
                send_error = False
                if res_line['CodigoErrorRegistro']:
                    send_error = u"{} | {}".format(
                        unicode(res_line['CodigoErrorRegistro']),
                        unicode(res_line['DescripcionErrorRegistro'])[:60])
                values = {
                    'sii_return': res,
                    'sii_send_error': send_error,
                }
                if res['EstadoEnvio'] == 'Correcto':
                    values['sii_sent'] = True
                    values['sii_csv'] = res['CSV']
                else:
                    values['sii_sent'] = False

                self.write(cr, uid, invoice.id, values)

            except Exception as fault:
                values = {
                    'sii_send_error': fault,
                    'sii_return': fault,
                }
                self.write(cr, uid, invoice.id, values)

    def invoice_validate(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
        for invoice in self.browse(cr, uid, ids):
            company = invoice.company_id
            #TODO sii_method auto
            if company.sii_enabled and self.is_sii_invoice(cr, uid, invoice):
                if not company.use_connector:
                    self._send_invoice_to_sii(cr, uid, [invoice.id])
                else:
                    #TODO
                    raise osv.except_osv(_('Error!'),
                                         _('Connector is not available'))
                    #eta = company._get_sii_eta()
                    # session = ConnectorSession.from_env(self.env)
                    # new_delay = confirm_one_invoice.delay(
                    #     session, 'account.invoice', invoice.id, eta=eta)
                    # invoice.invoice_jobs_ids |= queue_obj.search([
                    #     ('uuid', '=', new_delay)
                    # ], limit=1)

        return res

    def send_sii(self, cr, uid, ids, context=None):
        for invoice in self.browse(cr, uid, ids):
            if not self.is_sii_invoice(cr, uid, invoice):
                continue

            company = invoice.company_id
            if company.sii_enabled:
                if not company.use_connector:
                    self._send_invoice_to_sii(cr, uid, [invoice.id])
            else:
                #TODO
                eta = company._get_sii_eta()
                raise osv.except_osv(_('Error!'),
                                     _('Connector is not available'))
                # session = ConnectorSession.from_env(self.env)
                # new_delay = confirm_one_invoice.delay(
                #     session, 'account.invoice', invoice.id, eta=eta)
                # queue_ids = queue_obj.search([
                #     ('uuid', '=', new_delay)
                # ], limit=1)
                # invoice.invoice_jobs_ids |= queue_ids
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        #TODO
        # for queue in self.invoice_jobs_ids:
        #     if queue.state == 'started':
        #         raise exceptions.Warning(_(
        #             'You can not cancel this invoice because'
        #             ' there is a job running!'))
        #     elif queue.state in ('pending', 'enqueued', 'failed'):
        #         queue.write({
        #             'state': 'done',
        #             'date_done': date.today()})
        return super(account_invoice, self).action_cancel()

    def _get_sii_gen_type(self, cr, uid, invoice, context=None):
        """Make a choice for general invoice type
        Returns:
            int: 1 (National), 2 (Intracom), 3 (Export)
        """

        if invoice.fiscal_position.name == u'Régimen Intracomunitario':
            return 2
        elif invoice.fiscal_position.name == \
                u'Régimen Extracomunitario / Canarias, Ceuta y Melilla':
            return 3
        else:
            return 1

    def _get_sii_identifier(self, cr, uid, invoice_id, context=None):
        """Get the SII structure for a partner identifier depending on the
        conditions of the invoice.
        """
        invoice = self.browse(cr, uid, invoice_id)
        gen_type = self._get_sii_gen_type(cr, uid, invoice)
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
                    "CodigoPais": invoice.partner_id.country_id.code or vat[:2],
                    "IDType": '04',
                    "ID": vat,
                },
            }

    def _get_sii_exempt_cause(self, cr, uid, invoice, product_id, context=None):
        """Código de la causa de exención según 3.6 y 3.7 de la FAQ del SII."""
        gen_type = self._get_sii_gen_type(cr, uid, invoice)
        product = self.pool.get('product.template').browse(cr, uid, product_id)
        if gen_type == 2:
            return 'E5'
        elif gen_type == 3:
            return 'E2'
        # elif product.sii_exempt_cause != 'none':
        #     return product.sii_exempt_cause
        else:
            return False

    def is_sii_invoice(self, cr, uid, invoice, context=None):
        """Hook method to be overridden in additional modules to verify
        if the invoice must be sended trough SII system, for special cases.
        :param self: Single invoice record
        :return: bool value indicating if the invoice should be sent to SII.
        """
        if invoice.fiscal_position and not invoice.fiscal_position.sii_active:
            return False

        return True

    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None, description=None, journal_id=None, context=None):
        res = super(account_invoice, self)._prepare_refund(cr, uid, invoice,
                                                date=date,
                                                period_id=period_id,
                                                description=description,
                                                journal_id=journal_id,
                                                context=context
        )
        sii_refund_type = invoice.sii_refund_type
        if sii_refund_type:
            res['sii_refund_type'] = sii_refund_type

        return res
    
    def copy(self, cr, uid, id, default, context={}):

        default['sii_sent'] = False
        default['sii_csv'] = None
        default['sii_return'] = None

        return super(account_invoice, self).copy(cr, uid, id, default, context=context)

account_invoice()


class account_invoice_line(osv.Model):
    _inherit = 'account.invoice.line'

    def _get_sii_line_price_subtotal(self, cr, uid, invoice_line_id, context=None):
        invoice_line = self.browse(cr, uid, invoice_line_id)
        return invoice_line.price_unit * (1 - (invoice_line.discount or 0.0 ) / 100.0)

    def _get_sii_tax_line_req(self, cr, uid, code, invoice_line):
        taxes_re = self.pool.get('account.invoice')._get_sii_taxes_map(cr, uid, ['RE'], invoice_line.invoice_id)
        line = invoice_line
        if line.invoice_line_tax_id in taxes_re:
            price = self._get_sii_line_price_subtotal(cr, uid, line.id)
            taxes = self.pool.get('account.tax').compute_all(cr, uid, [line.tax], price, line.quantity,
                                                             line.product_id,
                                                             line.invoice_id.partner_id)
            taxes['percetage'] = line.tax.amount

            return taxes

        return {}

    def _update_sii_tax_line(self, cr, uid, tax_dict, tax_line, line):
        if tax_line.child_depend:
            tax_type = sum( child.amount for child in tax_line.child_ids)
        else:
            tax_type = tax_line.amount

        if tax_type not in tax_dict:
            tax_dict[tax_type] = {
                'TipoImpositivo': str(tax_type * 100),
                'BaseImponible': 0,
                'CuotaRepercutida': 0,
                'CuotaSoportada': 0,
            }
        tax_line_req = self._get_sii_tax_line_req(cr, uid, tax_type, line)
        if tax_line_req:
            tipo_recargo = tax_line_req['percentage'] * 100
            cuota_recargo = tax_line_req['taxes'][0]['amount']
            tax_dict[tax_type]['TipoRecargoEquivalencia'] = tipo_recargo
            tax_dict[tax_type].setdefault('CuotaRecargoEquivalencia', 0)
            tax_dict[tax_type]['CuotaRecargoEquivalencia'] += cuota_recargo

        taxes = self.pool.get('account.tax').compute_all(cr, uid, line.invoice_line_tax_id,
                                                         self._get_sii_line_price_subtotal(cr, uid, line.id), line.quantity,
                                                         line.product_id, line.invoice_id.partner_id.id)

        tax_dict[tax_type]['BaseImponible'] += taxes['total']

        if line.invoice_id.type in ['out_invoice', 'out_refund']:
            key = 'CuotaRepercutida'
        else:
            key = 'CuotaSoportada'
        tax_dict[tax_type][key] += taxes['taxes'][0]['amount']

        return tax_dict

account_invoice_line()
