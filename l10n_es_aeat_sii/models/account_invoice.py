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

import logging

from openerp.osv import fields, osv
from requests import Session
from zeep import Client
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from datetime import datetime
from tools.translate import _


_logger = logging.getLogger(__name__)


SII_STATES = [
    ('not_sent', 'Not sent'),
    ('sent', 'Sent'),
    ('sent_modified', 'Registered in SII but last modifications not sent'),
    ('cancelled', 'Cancelled'),
    ('cancelled_modified', 'Cancelled in SII but last modifications not sent'),
]


class account_invoice(osv.Model):
    _inherit = 'account.invoice'

    def _default_sii_refund_type(self, cr, uid, ids, context=None):
        if not context:
            context = {}

        return 'S' if context.get('invoice_type',False) in ('out_refund', 'in_refund') else False

    def _default_sii_registration_key(self, cr, uid, ids, context=None):
        sii_key_obj = self.pool.get('aeat.sii.mapping.registration.keys')
        if not context:
            context = {}

        if context.get('invoice_type',False) in ['in_invoice', 'in_refund']:
            key = sii_key_obj.search(cr, uid, [('code', '=', '01'), ('type', '=', 'purchase')], limit=1)
        else:
            key = sii_key_obj.search(cr, uid, [('code', '=', '01'), ('type', '=', 'sale')], limit=1)

        return key and key[0] or False

    _columns = {
        'sii_description': fields.text('SII Description', required=True),
        'sii_state': fields.selection(SII_STATES, 'SII Send state', help="Indicates the state of this invoice in "
                                                                         "relation with the presentation at the SII"),
        'sii_csv': fields.char(string='SII CSV', readonly=True),
        'sii_return': fields.text('SII Return', readonly=True),
        'sii_send_error': fields.text('SII Send Error', readonly=True),
        'sii_send_failed': fields.boolean('SII send failed',
                                          help="Indicates that the last attempt to communicate this invoice to "
                                               " the SII has failed. See SII return for details"),
        'sii_refund_type': fields.selection([('S', 'By substitution'), ('I', 'By differences')], 'Refund Type'),
        'sii_registration_key': fields.many2one('aeat.sii.mapping.registration.keys', 'SII registration key'),
        'sii_enabled': fields.related('company_id', 'sii_enabled',
                                      type='boolean',
                                      relation='res.company',
                                      string='SII Enabled',
                                      help='Enable SII for this fiscal position?',
                                      store=True,
                                      readonly=True),
    }

    _defaults = {
     'sii_state': 'not_sent',
     'sii_registration_key': _default_sii_registration_key,
     'sii_refund_type': _default_sii_refund_type,
     'sii_description': '/'
    }

    # TODO
    def onchange_refund_type(self, cr, uid, sii_refund_type, origin_invoices_ids):
        if sii_refund_type == 'S' and not origin_invoices_ids:
            sii_refund_type = False
            return {'warning':
                {'message':_('You must have at least one refunded invoice'),
                 }
            }

    def onchange_fiscal_position_l10n_es_aeat_sii(self, cr, uid, fiscal_position, invoice_type, context=None):
        if not fiscal_position:
            return False

        fiscal_position = self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position)
        if 'out' in invoice_type:
            key = fiscal_position.sii_registration_key_sale.id
        else:
            key = fiscal_position.sii_registration_key_purchase.id

        return key and key[0] or False

    def create(self, cr, uid, vals, context=None):
        if vals.get('fiscal_position') and not vals.get('sii_registration_key'):
            vals['sii_registration_key'] = self.\
                onchange_fiscal_position_l10n_es_aeat_sii(cr, uid, vals['fiscal_position'], context.get('type'))

        return super(account_invoice, self).create(cr, uid, vals, context)

    #TODO
    def write(self, cr, uid, ids, vals, context=None):
        """For supplier invoices the SII primary key is the supplier
        VAT/ID Otro and the supplier invoice number. Cannot let change these
        values in a SII registered supplier invoice"""
        if isinstance(ids, (int, long)):
            ids = [ids]

        for invoice in self.browse(cr, uid, ids, context):
            if (invoice.type in ['in_invoice', 'in refund'] and invoice.sii_state != 'not_sent'):
                if 'partner_id' in vals:
                    raise osv.except_osv(_('Warning!'),
                                         _("You cannot change the supplier of an invoice "
                                            "already registered at the SII. You must cancel the "
                                            "invoice and create a new one with the correct "
                                            "supplier"))

                elif 'supplier_invoice_number' in vals:
                    raise osv.except_osv(_('Warning!'),
                        _("You cannot change the supplier invoice number of "
                          "an invoice already registered at the SII. You must "
                          "cancel the invoice and create a new one with the "
                          "correct number")
                    )

            if vals.get('fiscal_position') and not vals.get('sii_registration_key'):
                vals['sii_registration_key'] = self.\
                    onchange_fiscal_position_l10n_es_aeat_sii(cr, uid, vals.get('fiscal_position'),
                                                                             invoice.type)

        return super(account_invoice, self).write(cr, uid, ids, vals)

    def unlink(self, cr, uid, ids, context=None):
        """A registered invoice at the SII cannot be deleted"""
        for invoice in self.browse(cr, uid, ids, context):
            if invoice.sii_state != 'not_sent':
                raise osv.except_osv(_('Warning!'),
                    _("You cannot delete an invoice already registered at the "
                      "SII.")
                )
        return super(account_invoice, self).unlink(cr, uid, ids, context)

    def map_sii_tax_template(self, cr, uid, tax_template, mapping_taxes, invoice):
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
             '|', ('date_to', '>=', invoice.date_invoice), ('date_to', '=', False)], limit=1))

        if sii_map:
            mapping_taxes = {}
            for code in codes:
                sii_map_line_id = sii_map_line_obj.search(cr, uid, [('code', '=', code),
                                                                    ('sii_map_id', '=', sii_map[0].id)])
                if sii_map_line_id:
                    tax_search_obj = sii_map_line_obj.browse(cr, uid, sii_map_line_id[0])
                    tax_templates = tax_search_obj and tax_search_obj.taxes or []
                    for tax_template in tax_templates:
                        tax = self.map_sii_tax_template(cr, uid, tax_template, mapping_taxes, invoice)
                        if tax:
                            taxes.append(tax)

        return self.pool.get("account.tax").browse(cr, uid, taxes)

    def _change_date_format(self, cr, uid, date):
        date_time_object = datetime.strptime(date, '%Y-%m-%d')
        new_date = date_time_object.strftime('%d-%m-%Y')

        return new_date
    
    
    def _get_sii_header(self, cr, uid, ids, company, comunication_type=False, cancellation=False):
        """Builds SII send header
        :param comunication_type String 'A0': new reg, 'A1': modification
        :param cancellation Bool True when the communitacion es for invoice
            cancellation
        :return Dict with header data depending on cancellation
        """
        if not company.partner_id.vat:
            raise osv.except_osv(_('Warning!'),
                                 _("No VAT configured for the company '{}'").format(company.name))

        header = { "IDVersionSii": company.version_sii,
                   "Titular": {
                      "NombreRazon": company.name,
                      "NIF": company.vat[2:]},
        }

        if not cancellation:
            header.update({"TipoComunicacion": comunication_type})

        return header
    
    def _get_sii_out_taxes(self, cr, uid, invoice, context=None):
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
        default_no_taxable_cause = self._get_no_taxable_cause(cr, uid, invoice.fiscal_position.id)

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
                            self.pool.get('account.invoice.line').
                                _get_sii_line_price_subtotal(cr, uid, line.id)
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
                        taxes_f = self.pool.get('account.invoice.line').\
                            _update_sii_tax_line(cr, uid, taxes_f, tax_line, line)

                # No sujetas
                if tax_line in taxes_sfens:
                    nsub_dict = tax_breakdown.setdefault(
                        'NoSujeta', {default_no_taxable_cause: 0},
                    )
                    nsub_dict[default_no_taxable_cause] += self.pool.get('account.invoice.line').\
                        _get_sii_line_price_subtotal(cr, uid, line.id )

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

                        exempt_dict['BaseImponible'] += self.pool.get('account.invoice.line').\
                            _get_sii_line_price_subtotal(cr, uid, line.id)

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

                        taxes_to = self.pool.get('account.invoice.line').\
                            _update_sii_tax_line(cr, uid, taxes_to, tax_line, line)

        sign = -1.0 if invoice.sii_refund_type == 'I' else 1.0
        for val in taxes_f.values() + taxes_to.values():
            val['CuotaRepercutida'] = round(val['CuotaRepercutida'] * sign, 2)
            val['BaseImponible'] = round(val['BaseImponible'] * sign, 2)
            if 'CuotaRecargoEquivalencia' in val:
                val['CuotaRecargoEquivalencia'] = round(val['CuotaRecargoEquivalencia'] * sign, 2)

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
            taxes_dict['DesgloseTipoOperacion']['Entrega'] = taxes_dict['DesgloseFactura']
            del taxes_dict['DesgloseFactura']

        return taxes_dict

    def _get_sii_in_taxes(self, cr, uid, invoice): 
        taxes_dict = {}
        taxes_f = {}
        taxes_isp = {}
        taxes_sfrs = self._get_sii_taxes_map(cr, uid, ['SFRS'], invoice)
        taxes_sfrisp = self._get_sii_taxes_map(cr, uid, ['SFRISP'], invoice)
        taxes_sfrns = self._get_sii_taxes_map(cr, uid, ['SFRNS'], invoice)
        tax_amount = 0.0

        for line in invoice.invoice_line:
            for tax_line in line.invoice_line_tax_id:
                if tax_line in taxes_sfrisp:
                    self.pool.get('account.invoice.line')._update_sii_tax_line(cr, uid, taxes_isp, tax_line, line)
                elif tax_line in taxes_sfrs:
                    self.pool.get('account.invoice.line')._update_sii_tax_line(cr, uid, taxes_f, tax_line, line)
                elif tax_line in taxes_sfrns:
                    nsub_dict = taxes_dict.setdefault(
                        'DesgloseIVA',
                        {'DetalleIVA': {'BaseImponible': 0}},
                    )
                    nsub_dict['DetalleIVA']['BaseImponible'] += \
                        self.pool.get('account.invoice.line')._get_sii_line_price_subtotal(cr, uid, line.id)

        if taxes_isp:
            taxes_dict.setdefault(
                'InversionSujetoPasivo', {'DetalleIVA': taxes_isp.values()},
            )

        if taxes_f:
            taxes_dict.setdefault(
                'DesgloseIVA', {'DetalleIVA': taxes_f.values()},
            )

        sign = -1.0 if invoice.sii_refund_type == 'I' else 1.0
        for val in taxes_isp.values() + taxes_f.values():
            val['CuotaSoportada'] = round(val['CuotaSoportada'] * sign, 2)
            val['BaseImponible'] = round(val['BaseImponible'] * sign, 2)
            if 'CuotaRecargoEquivalencia' in val:
                val['CuotaRecargoEquivalencia'] = round(val['CuotaRecargoEquivalencia'] * sign, 2)

            tax_amount += val['CuotaSoportada']

        return taxes_dict, tax_amount

    def _sii_check_exceptions(self, cr, uid, invoice_id, context=None):
        """Inheritable method for exceptions control when sending SII invoices.
        """
        invoice = self.browse(cr, uid, invoice_id)
        if not invoice.partner_id.vat:
            raise osv.except_osv(_('Warning!'),
                _('The partner has not a VAT configured.')
            )
        # if not invoice.company_id.chart_template_id:
        #     raise osv.except_osv(_('Warning!'),
        #         _('You have to select what account chart template use this company.'))

        if not invoice.company_id.sii_enabled:
            raise osv.except_osv(_('Warning!'),
                _('This company doesn\'t have SII enabled.')
            )

        if not invoice.sii_enabled:
            raise osv.except_osv(_('Warning!'),
                                 _('This invoice is not SII enabled.')
                                 )

    def _get_account_registration_date(self):
        """Hook method to allow the setting of the account registration date
        of each supplier invoice. The SII recommends to set the send date as
        the default value (point 9.3 of the document
        SII_Descripcion_ServicioWeb_v0.7.pdf), so by default we return
        the current date
        :return String date in the format %Y-%m-%d"""
        return datetime.today().strftime("%Y-%m-%d")
    
    def _get_sii_invoice_dict_out(self, cr, uid, invoice_id, cancel=False, context=None):
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
                "NumSerieFacturaEmisor": (invoice.number or invoice.internal_number or '')[0:60],
                "FechaExpedicionFacturaEmisor": invoice_date
            },
            "PeriodoImpositivo": {
                "Ejercicio": ejercicio,
                "Periodo": periodo,
            },
        }

        if not cancel:
            # Check if refund type is 'By differences'. Negative amounts!
            sign = -1.0 if invoice.sii_refund_type == 'I' else 1.0
            inv_dict["FacturaExpedida"] = {
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
                "ImporteTotal": invoice.cc_amount_total * sign,
            }

            exp_dict = inv_dict['FacturaExpedida']
            # Uso condicional de IDOtro/NIF
            exp_dict['Contraparte'].update(self._get_sii_identifier(cr, uid, invoice.id))
            if invoice.type == 'out_refund':
                exp_dict['TipoRectificativa'] = invoice.sii_refund_type
                if invoice.sii_refund_type == 'S':
                    exp_dict['ImporteRectificacion'] = {
                        'BaseRectificada': invoice.cc_amount_untaxed,
                        'CuotaRectificada': invoice.cc_amount_tax,
                    }

        return inv_dict

    def _get_sii_invoice_dict_in(self, cr, uid, invoice_id, cancel=False, context=None):
        invoice = self.browse(cr, uid, invoice_id)
        invoice_date = self._change_date_format(cr, uid, invoice.date_invoice)
        reg_date = self._change_date_format(cr, uid,
            self._get_account_registration_date(),
        )
        if invoice.period_id.fiscalyear_id.date_start[0:4] == invoice.period_id.fiscalyear_id.date_stop[0:4]:
            ejercicio = invoice.period_id.fiscalyear_id.date_start[0:4]
        else:
            ejercicio = invoice.period_id.date_start[0:4]

        periodo = invoice.period_id.date_start[5:7]

        desglose_factura, tax_amount = self._get_sii_in_taxes(cr, uid, invoice)

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
        }

        ident = self._get_sii_identifier(cr, uid, invoice_id)
        inv_dict['IDFactura']['IDEmisorFactura'].update(ident)

        if cancel:
            inv_dict['IDFactura']['IDEmisorFactura'].update(
                {'NombreRazon': self.partner_id.name[0:120]}
            )
        else:
            # Check if refund type is 'By differences'. Negative amounts!
            sign = -1.0 if invoice.sii_refund_type == 'I' else 1.0
            inv_dict["FacturaRecibida"] = {
                    # TODO: Incluir los 5 tipos de facturas rectificativas
                    "TipoFactura": (
                        'R4' if invoice.type == 'in_refund' else 'F1'
                    ),
                    "ClaveRegimenEspecialOTrascendencia": (
                        invoice.sii_registration_key.code
                    ),
                    "DescripcionOperacion": invoice.sii_description[0:500],
                    "DesgloseFactura": desglose_factura,
                    "Contraparte": {
                        "NombreRazon": invoice.partner_id.name[0:120],
                    },
                    "FechaRegContable": reg_date,
                    "ImporteTotal": invoice.cc_amount_total * sign,
                    "CuotaDeducible": round(tax_amount * sign, 2),
            }

            inv_dict['FacturaRecibida']['Contraparte'].update(ident)
            if invoice.type == 'in_refund':
                rec_dict = inv_dict['FacturaRecibida']
                rec_dict['TipoRectificativa'] = invoice.sii_refund_type
                if invoice.sii_refund_type == 'S':
                    refund_tax_amount = sum([self._get_sii_in_taxes(cr, uid, x)[1] for x in invoice.origin_invoices_ids])
                    rec_dict['ImporteRectificacion'] = {
                        'BaseRectificada': invoice.cc_amount_untaxed,
                        'CuotaRectificada': refund_tax_amount,
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

    def _get_cancel_sii_invoice_dict(self, cr, uid, invoice_id, context=None):
        self._sii_check_exceptions(cr, uid, invoice_id)
        invoice = self.browse(cr, uid, invoice_id, context)
        if invoice.type in ['out_invoice', 'out_refund']:
            return self._get_sii_invoice_dict_out(cr, uid, invoice_id, cancel=True)
        elif invoice.type in ['in_invoice', 'in_refund']:
            return self._get_sii_invoice_dict_in(cr, uid, invoice_id, cancel=True)

    def _connect_sii(self, cr, uid, wsdl, company_id, context=None):
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
    
    def _send_invoice_to_sii(self, cr, uid, ids, context=None):
        for invoice in self.browse(cr, uid, ids):
            company = invoice.company_id
            port_name = ''
            wsdl = ''
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
            if invoice.sii_state == 'not_sent':
                tipo_comunicacion = 'A0'
            else:
                tipo_comunicacion = 'A1'

            header = self._get_sii_header(cr, uid, invoice.id, company, tipo_comunicacion)
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
                    values['sii_state'] = 'sent'
                    values['sii_csv'] = res['CSV']
                    values['sii_send_failed'] = False
                else:
                    values['sii_send_failed'] = True

                self.write(cr, uid, invoice.id, values)

            except Exception as fault:
                values = {
                    'sii_send_failed': True,
                    'sii_send_error': True,
                    'sii_return': fault,
                }
                self.write(cr, uid, invoice.id, values)


    def invoice_validate(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
        for invoice in self.browse(cr, uid, ids):
            if invoice.sii_enabled:
                values = {}
                if invoice.sii_state == 'sent':
                    values['sii_state'] = 'sent_modified'
                elif invoice.sii_state == 'cancelled':
                    values['sii_state'] = 'cancelled_modified'

                if values:
                    self.write(cr, uid, ids, values, context)

                company = invoice.company_id
                if company.sii_method != 'auto':
                    continue

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

    def _cancel_invoice_to_sii(self, cr, uid, ids, context=None):
        for invoice in self.browse(cr, uid, ids):
            company = invoice.company_id
            port_name = ''
            wsdl = ''
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

            header = self._get_sii_header(cr, uid, invoice.id, company, cancellation=True)
            inv_dict = self._get_cancel_sii_invoice_dict(cr, uid, invoice.id)
            _logger.debug("header %s" %header)
            _logger.debug("inv_dict %s" %inv_dict)

            try:

                if invoice.type in ['out_invoice','out_refund']:
                    res = serv.AnulacionLRFacturasEmitidas(header, inv_dict)
                elif invoice.type in ['in_invoice','in_refund']:
                    res = serv.AnulacionLRFacturasRecibidas(header, inv_dict)
                # TODO Facturas intracomunitarias 66 RIVA
                # elif invoice.fiscal_position.id == self.env.ref(
                #     'account.fp_intra').id:
                #     res = serv.AnulacionLRDetOperacionIntracomunitaria(
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
                    values['sii_state'] = 'cancelled'
                    values['sii_csv'] = res['CSV']
                    values['sii_send_failed'] = False
                else:
                    values['sii_send_failed'] = True

                self.write(cr, uid, invoice.id, values)

            except Exception as fault:
                values = {
                    'sii_send_error': fault,
                    'sii_return': fault,
                }
                self.write(cr, uid, invoice.id, values)

    def cancel_sii(self, cr, uid, ids, context=None):
        # if not invoices._cancel_invoice_jobs():
        #     raise osv.except_osv(_('Warning!'),
        #         'You can not communicate the cancellation of this invoice '
        #         'at this moment because there is a job running!'))
        #queue_obj = self.env['queue.job']
        for invoice in self.browse(cr, uid, ids, context):
            if (invoice.sii_enabled and invoice.state in ['cancel'] and
                       invoice.sii_state in ['sent', 'sent_modified']):
                company = invoice.company_id
                if not company.use_connector:
                    self._cancel_invoice_to_sii(cr, uid, ids)
                else:
                    raise osv.except_osv(_('Error!'),
                                         _('Connector is not available'))
            # else:
            #     eta = company._get_sii_eta()
            #     session = ConnectorSession.from_env(self.env)
            #     new_delay = cancel_one_invoice.delay(
            #         session, 'account.invoice', invoice.id, eta=eta)
            #     queue_ids = queue_obj.search([
            #         ('uuid', '=', new_delay)
            #     ], limit=1)
            #     invoice.invoice_jobs_ids |= queue_ids

        return True

    #TODO
    # def _cancel_invoice_jobs(self):
    #     for invoice in self:
    #         for queue in invoice.invoice_jobs_ids:
    #             if queue.state == 'started':
    #                 return False
    #             elif queue.state in ('pending', 'enqueued', 'failed'):
    #                 queue.write({
    #                     'state': 'done',
    #                     'date_done': date.today()})
    #     return True

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
        for invoice in self.browse(cr, uid, ids, context):
            values = {}
            if invoice.sii_state == 'sent':
                values['sii_state'] = 'sent_modified'
            elif invoice.sii_state == 'cancelled_modified':
                values['sii_state'] = 'cancelled'

            if values:
                self.write(cr, uid, invoice.id, values)

        return super(account_invoice, self).action_cancel(cr, uid, ids, context)

    # TODO
    # def action_cancel_draft(self, cr, uid, ids, *args):
    #     if not self._cancel_invoice_jobs():
    #         raise osv.except_osv(_(
    #             'You can not set to draft this invoice because'
    #             ' there is a job running!'))
    #
    #     return super(account_invoice, self).action_cancel_draft(cr, uid, ids)

    def _get_sii_gen_type(self, cr, uid, invoice, context=None):
        """Make a choice for general invoice type
        Returns:
            int: 1 (National), 2 (Intracom), 3 (Export)
        """
        if u'Régimen Intracomunitario' in invoice.fiscal_position.name :
            return 2
        elif u'Régimen Extracomunitario' in invoice.fiscal_position.name:
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
        elif product.sii_exempt_cause != 'none':
            return product.sii_exempt_cause
        elif invoice.fiscal_position and \
                invoice.fiscal_position.sii_exempt_cause != 'none':
            return invoice.fiscal_position.sii_exempt_cause

        return False

    def _get_no_taxable_cause(self, cr, uid, fiscal_position_id, context=None):
        fiscal_position = self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position_id)

        return fiscal_position.sii_no_taxable_cause or \
            'ImportePorArticulos7_14_Otros'
    #TODO
    # def _compute_sii_enabled(self, cr, uid, ids):
    #     """Compute if the invoice is enabled for the SII"""
    #
    #     for invoice in self:
    #         if invoice.company_id.sii_enabled:
    #             invoice.sii_enabled = (
    #                 (invoice.fiscal_position and
    #                  invoice.fiscal_position.sii_active) or
    #                 not invoice.fiscal_position
    #             )
    #         else:
    #             invoice.sii_enabled = False


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
        default['sii_state'] = False
        default['sii_csv'] = None
        default['sii_return'] = None
        default['sii_send_error'] = None

        return super(account_invoice, self).copy(cr, uid, id, default, context=context)

account_invoice()


class account_invoice_line(osv.Model):
    _inherit = 'account.invoice.line'

    def _get_sii_line_price_unit(self, cr, uid, invoice_line_id, context=None):
        line = self.browse(cr, uid, invoice_line_id, context)
        price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

        if line.invoice_id.currency_id != line.invoice_id.company_id.currency_id:
            from_currency = line.invoice_id.currency_id.id
            price_unit = self.pool.get('res.currency'). \
                compute(cr, uid, from_currency, line.invoice_id.company_id.currency_id.id, price_unit)

        return price_unit

    def _get_sii_line_price_subtotal(self, cr, uid, invoice_line_id, context=None):
        invoice_line = self.browse(cr, uid, invoice_line_id)
        return self._get_sii_line_price_unit(cr, uid, invoice_line.id) * invoice_line.quantity

    def _get_sii_tax_line_req(self, cr, uid, code, invoice_line):
        taxes_re = self.pool.get('account.invoice')._get_sii_taxes_map(cr, uid, ['RE'], invoice_line.invoice_id)
        line = invoice_line
        if line.invoice_line_tax_id in taxes_re:
            taxes = self.pool.get('account.tax').compute_all(cr, uid, line.invoice_line_tax_id,
                                                             self._get_sii_line_price_unit(cr, uid, line.id), line.quantity,
                                                             line.product_id,
                                                             line.invoice_id.partner_id)
            taxes['percetage'] = line.tax.amount

            return taxes

        return {}

    def _update_sii_tax_line(self, cr, uid, tax_dict, tax_line, line):
        if tax_line.child_depend:
            tax_type = sum(child.amount for child in tax_line.child_ids)
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
                                                         self._get_sii_line_price_unit(cr, uid, line.id), line.quantity,
                                                         line.product_id, line.invoice_id.partner_id.id)

        tax_dict[tax_type]['BaseImponible'] += taxes['total']

        if line.invoice_id.type in ['out_invoice', 'out_refund']:
            key = 'CuotaRepercutida'
        else:
            key = 'CuotaSoportada'
        tax_dict[tax_type][key] += taxes['taxes'][0]['amount']
        return tax_dict

account_invoice_line()