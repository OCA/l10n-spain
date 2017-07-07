# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Studio73 - Pablo Fuentes <pablo@studio73>
# Copyright 2017 Studio73 - Jordi Tolsà <jordi@studio73.es>
# Copyright 2017 Alberto Martín Cortada <alberto.martin@guadaltech.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from datetime import date, datetime
from requests import Session

from openerp.osv import osv, fields
from openerp import exceptions
import pooler
from openerp.tools.float_utils import float_round

_logger = logging.getLogger(__name__)

try:
    from zeep import Client
    from zeep.transports import Transport
    from zeep.plugins import HistoryPlugin
except (ImportError, IOError) as err:
    _logger.debug(err)


from openerp.tools.translate import _

SII_STATES = [
    ('not_sent', 'Not sent'),
    ('sent', 'Sent'),
    ('sent_modified', 'Registered in SII but last modifications not sent'),
    ('cancelled', 'Cancelled'),
    ('cancelled_modified', 'Cancelled in SII but last modifications not sent'),
]

SII_VERSION = '1.0'
SII_START_DATE = '2017-07-01'


class AccountInvoice(osv.Model):
    _inherit = 'account.invoice'

    def _default_sii_refund_type(self, cr, uid,context=None):
        if context is None:
            context = {}
        inv_type = context.get('default_type')
        return 'S' if inv_type in ['out_refund', 'in_refund'] else False

    def _default_sii_registration_key(self, cr, uid, context=None):
        if context is None:
            context = {}

        sii_key_obj = self.pool['aeat.sii.mapping.registration.keys']
        inv_type = context.get('default_type')
        if inv_type in ['in_invoice', 'in_refund']:
            key = sii_key_obj.search(cr, uid,
                                     [('code', '=', '01'), ('type', '=', 'purchase')], limit=1)
        else:
            key = sii_key_obj.search(cr, uid,
                                     [('code', '=', '01'), ('type', '=', 'sale')], limit=1)
        return key and key[0]

    def _default_sii_description(self, cr, uid, context=None):


        inv_type = context.get('default_type')
        if context.get('force_company'):
            company = self.pool['res.company'].browse(cr, uid, context['force_company'])
        else:
            company = self.pool.get("res.users").browse(cr,uid, uid).company_id

        method_desc = company.sii_description_method
        header_customer = company.sii_header_customer
        header_supplier = company.sii_header_supplier

        description = ''
        if inv_type in ['out_invoice', 'out_refund'] and header_customer:
            description = header_customer
        elif inv_type in ['in_invoice', 'in_refund'] and header_supplier:
            description = header_supplier
        if method_desc in ['fixed']:
            fixed_desc = company.sii_description
            if fixed_desc and description:
                description += ' | '
            description += fixed_desc
        return description[0:500] or '/'


    def _compute_sii_enabled(self, cr, uid, ids, name, arg={}, context=None):
        """Compute if the invoice is enabled for the SII"""
        result = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.company_id.sii_enabled:
                enabled = (
                    (invoice.fiscal_position and
                     invoice.fiscal_position.sii_active) or
                    not invoice.fiscal_position
                )
            else:
                enabled = False

            result[invoice.id] = enabled
        return result

    _columns = {

        'sii_description': fields.text(string='SII Description', required=False),
        'sii_state': fields.selection(
            selection=SII_STATES, string="SII send state", default='not_sent',
            help="Indicates the state of this invoice in relation with the "
                 "presentation at the SII",
        ),
        'sii_sent': fields.boolean(string='SII Sent'),
        'sii_return': fields.text(string='SII Return'),
        'sii_send_error': fields.text(
            string='SII Send Error', readonly=True,
        ),
        'sii_send_failed': fields.boolean(
            string="SII send failed",
            help="Indicates that the last attempt to communicate this invoice to "
                 "the SII has failed. See SII return for details",
        ),

        'sii_refund_type': fields.selection(
            selection=[('S', 'By substitution'), ('I', 'By differences')],
            string="Refund Type"),
        'sii_registration_key': fields.many2one('aeat.sii.mapping.registration.keys', "Registration key", required=False),
        'sii_csv': fields.char(string='SII CSV', size=64),
        'sii_enabled': fields.function(_compute_sii_enabled, type='boolean', string='Enable SII'),

    }

    _defaults = {
        'sii_registration_key': _default_sii_registration_key,
        'sii_refund_type': _default_sii_refund_type,
        'sii_description': _default_sii_description,
        'sii_state': 'not_sent',
    }

    def copy(self, cr, uid, id, default, context={}):

        default['sii_sent'] = False
        default['sii_return'] = None
        default['sii_csv'] = None
        default['sii_state'] = 'not_sent'
        default['sii_send_error'] = None

        return super(AccountInvoice, self).copy(cr, uid, id, default, context=context)

    def onchange_refund_type_l10n_es_aeat_sii(self, cr, uid, ids, refund_type):
        for invoice in self.browse(cr, uid, ids):
            if refund_type == 'S' and not invoice.origin_invoices_ids:
                return {'warning':
                            {'message': 'You must have at least one refunded invoice'},
                        'value': {
                            'sii_refund_type': None,
                        }
                        }

    def on_change_fiscal_position(self, cr, uid, ids, fiscal_position, type, context=None):
        """
        Suggest an operation key when fiscal position changes
        """
        if context is None:
            context = {}
        res = super(AccountInvoice, self).on_change_fiscal_position(cr, uid, ids, fiscal_position, type)
        if fiscal_position:
            fiscal_obj = self.pool.get('account.fiscal.position')
            fp = fiscal_obj.browse(cr, uid, [fiscal_position])[0]
            if 'out' in type:
                key = fp.sii_registration_key_sale
            else:
                key = fp.sii_registration_key_purchase
            res['value']['sii_registration_key'] = key and key.id or False


        return res

    def onchange_invoice_line_l10n_es_aeat_sii(self, cr, uid, ids, invoice_line):
        description = ""
        for invoice in self.browse(cr, uid, ids):
            if invoice.company_id.sii_description_method != 'auto':
                continue
            description = self._default_sii_description(cr,uid,{'default_type': invoice.type, 'force_company': invoice.company_id.id})
            if description:
                description += ' | '
            for line in invoice.invoice_line:
                description += ' - %s' % line.name

        return {
            'value': {
                'sii_description': description[:500],
            }
        }


    def write(self, cr, uid, ids, vals,context=None):
        """For supplier invoices the SII primary key is the supplier
        VAT/ID Otro and the supplier invoice number. Cannot let change these
        values in a SII registered supplier invoice"""

        if not isinstance(ids,list):
            ids = [ids]

        for invoice in self.browse(cr, uid, ids):
            if (invoice.type in ['in_invoice', 'in refund'] and
                    invoice.sii_state != 'not_sent'):
                if 'partner_id' in vals:
                    raise exceptions.Warning(
                        _("You cannot change the supplier of an invoice "
                          "already registered at the SII. You must cancel the "
                          "invoice and create a new one with the correct "
                          "supplier")
                    )
                elif 'reference' in vals:
                    raise exceptions.Warning(
                        _("You cannot change the supplier invoice number of "
                          "an invoice already registered at the SII. You must "
                          "cancel the invoice and create a new one with the "
                          "correct number")
                    )
        return super(AccountInvoice, self).write(cr, uid, ids, vals,context)


    def unlink(self,cr, uid, ids, context=None):
        """A registered invoice at the SII cannot be deleted"""
        for invoice in self.browse(cr, uid, ids):
            if invoice.sii_state in ['sent','sent_modified','cancelled', 'cancelled_modified']:
                raise exceptions.Warning(
                    _("You cannot delete an invoice already registered at the "
                      "SII.")
                )
        return super(AccountInvoice, self).unlink(cr, uid, ids)

    def map_sii_tax_template(self, cr, uid, tax_template, mapping_taxes, invoice):
        """Adds a tax template -> tax id to the mapping.
        Adapted from account_chart_update module.

        :param self: Single invoice record.
        :param tax_template: Tax template record.
        :param mapping_taxes: Dictionary with all the tax templates mapping.
        :return: Tax template current mapping
        """
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
            criteria = ['|'] + criteria
            criteria += ['|',
                         ('description', '=', tax_template.description),
                         ('name', '=', tax_template.description)]
        criteria += [('company_id', '=', invoice.company_id.id)]
        taxes = tax_obj.search(cr, uid, criteria, context=context)
        mapping_taxes[tax_template] = (
            taxes and taxes[0] or None)
        return mapping_taxes[tax_template]

    def _get_sii_taxes_map(self, cr, uid, codes, invoice):
        # Return the codes that correspond to that sii map line codes
        taxes = []
        sii_map_obj = self.pool['aeat.sii.map']
        sii_map_line_obj = self.pool['aeat.sii.map.lines']
        sii_map = sii_map_obj.browse(cr, uid, sii_map_obj.search(cr, uid,
                                                                 ['|',
                                                                  ('date_from', '<=', invoice.date_invoice,),
                                                                  ('date_from', '=', False),
                                                                  '|',
                                                                  ('date_to', '>=', invoice.date_invoice,),
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

    def _get_sii_header(self, cr, uid, ids, company, tipo_comunicacion=False, cancellation=False):

        if not company.vat:
            raise exceptions.Warning(_(
                "No VAT configured for the company '{}'").format(company.name))

        header = {
            "IDVersionSii": SII_VERSION,
            "Titular": {
                "NombreRazon": company.name[0:120],
                "NIF": company.vat[2:]},
            "TipoComunicacion": tipo_comunicacion
        }
        if not cancellation:
            header.update({"TipoComunicacion": tipo_comunicacion})
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
                                              ['SFESB'], invoice)
        taxes_sfesbe = self._get_sii_taxes_map(cr, uid,
                                               ['SFESBE'], invoice)
        taxes_sfesisp = self._get_sii_taxes_map(cr, uid,
                                                ['SFESISP'], invoice)
        #         taxes_SFESISPS = self._get_taxes_map(cr, uid,
        #             ['SFESISPS'], invoice)
        taxes_sfens = self._get_sii_taxes_map(cr, uid,
                                              ['SFENS'], invoice)
        taxes_sfess = self._get_sii_taxes_map(cr, uid,
                                              ['SFESS'], invoice)
        taxes_sfesse = self._get_sii_taxes_map(cr, uid,
                                               ['SFESSE'], invoice)

        default_no_taxable_cause = self._get_no_taxable_cause(cr, uid, invoice)
        # Check if refund type is 'By differences'. Negative amounts!
        sign = -1.0 if invoice.sii_refund_type == 'I' else 1.0
        for inv_line in invoice.invoice_line:
            exempt_cause = self._get_sii_exempt_cause(cr, uid, inv_line.product_id, invoice)
            for tax_line in inv_line.invoice_line_tax_id:
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
                            inv_line_obj._get_sii_line_price_subtotal(cr, uid, inv_line) * sign
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
                        inv_line_obj._update_sii_tax_line(cr, uid, inv_line, taxes_f, tax_line)
                # No sujetas
                if tax_line in taxes_sfens:
                    nsub_dict = tax_breakdown.setdefault(
                        'NoSujeta', {default_no_taxable_cause: 0},
                    )
                    nsub_dict[default_no_taxable_cause] += inv_line_obj._get_sii_line_price_subtotal(cr, uid, inv_line)
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
                        exempt_dict['BaseImponible'] += inv_line_obj._get_sii_line_price_subtotal(cr, uid, inv_line) * sign
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

        # Check if refund type is 'By differences'. Negative amounts!
        sign = -1.0 if invoice.sii_refund_type == 'I' else 1.0
        for val in taxes_f.values() + taxes_to.values():
            val['CuotaRepercutida'] = float_round(
                val['CuotaRepercutida'] * sign, 2,
            )
            val['BaseImponible'] = float_round(val['BaseImponible'] * sign, 2)
            if 'CuotaRecargoEquivalencia' in val:
                val['CuotaRecargoEquivalencia'] = float_round(
                    val['CuotaRecargoEquivalencia'] * sign, 2,
                )
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
                'DesgloseFactura' in taxes_dict) or
                ('DesgloseFactura' in taxes_dict
                 and self._get_sii_gen_type(cr, uid, invoice) in (2, 3))):
            taxes_dict.setdefault('DesgloseTipoOperacion', {})
            taxes_dict['DesgloseTipoOperacion']['Entrega'] = \
                taxes_dict['DesgloseFactura']
            del taxes_dict['DesgloseFactura']
        return taxes_dict

    def _get_sii_in_taxes(self, cr, uid, invoice):
        """Get the taxes for purchase invoices.

        :param self:  Single invoice record.
        """
        inv_line_obj = self.pool.get('account.invoice.line')

        taxes_dict = {}
        taxes_f = {}
        taxes_isp = {}
        taxes_sfrs = self._get_sii_taxes_map(cr, uid,
                                             ['SFRS'], invoice)
        taxes_sfrisp = self._get_sii_taxes_map(cr, uid,
                                               ['SFRISP'], invoice)
        taxes_sfrns = self._get_sii_taxes_map(cr, uid,
                                               ['SFRNS'], invoice)
        tax_amount = 0.0
        for inv_line in invoice.invoice_line:
            for tax_line in inv_line.invoice_line_tax_id:
                if tax_line in taxes_sfrisp:
                    inv_line_obj._update_sii_tax_line(cr, uid, inv_line, taxes_isp, tax_line)
                elif tax_line in taxes_sfrs:
                    inv_line_obj._update_sii_tax_line(cr, uid, inv_line, taxes_f, tax_line)
                elif tax_line in taxes_sfrns:
                    nsub_dict = taxes_dict.setdefault(
                        'DesgloseIVA',
                        {'DetalleIVA': {'BaseImponible': 0}},
                    )
                    nsub_dict['DetalleIVA']['BaseImponible'] +=\
                        inv_line_obj._get_sii_line_price_subtotal(cr, uid, inv_line) * sign

        if taxes_isp:
            taxes_dict.setdefault(
                'InversionSujetoPasivo', {'DetalleIVA': taxes_isp.values()},
            )
        if taxes_f:
            taxes_dict.setdefault(
                'DesgloseIVA', {'DetalleIVA': taxes_f.values()},
            )
        # Check if refund type is 'By differences'. Negative amounts!
        sign = -1.0 if invoice.sii_refund_type == 'I' else 1.0
        for val in taxes_isp.values() + taxes_f.values():
            val['CuotaSoportada'] = float_round(
                val['CuotaSoportada'] * sign, 2,
            )
            val['BaseImponible'] = float_round(val['BaseImponible'] * sign, 2)
            if 'CuotaRecargoEquivalencia' in val:
                val['CuotaRecargoEquivalencia'] = float_round(
                    val['CuotaRecargoEquivalencia'] * sign, 2,
                )
            tax_amount += val['CuotaSoportada']
        return taxes_dict, tax_amount


    def _sii_check_exceptions(self,cr, uid, invoice):
        """Inheritable method for exceptions control when sending SII invoices.
        """
        if not invoice.partner_id.vat and not invoice.partner_id.sii_simplified_invoice:
            raise exceptions.Warning(
                _("The partner has not a VAT configured.")
            )
        if not invoice.company_id.chart_template_id:
            raise exceptions.Warning(_(
                'You have to select what account chart template use this'
                ' company.'))
        if not invoice.company_id.sii_enabled:
            raise exceptions.Warning(
                _("This company doesn't have SII enabled.")
            )
        if not invoice.sii_enabled:
            raise exceptions.Warning(
                _("This invoice is not SII enabled.")
            )

        if not invoice.reference and invoice.type in ['in_invoice','in_refund']:
            raise exceptions.Warning(
                _("The supplier number invoice is required")
            )

        if invoice.partner_id.sii_simplified_invoice and invoice.type[:2] == 'in':
            raise exceptions.Warning(
                _("You can't make a supplier simplified invoice.")
                )


    def _get_account_registration_date(self, cr, uid, invoice):
        """Hook method to allow the setting of the account registration date
        of each supplier invoice. The SII recommends to set the send date as
        the default value (point 9.3 of the document
        SII_Descripcion_ServicioWeb_v0.7.pdf), so by default we return
        the current date
        :return String date in the format %Y-%m-%d"""
        return date.today().strftime("%Y-%m-%d")

    def _get_sii_invoice_dict_out(self, cr, uid, invoice, cancel=False):

        """Build dict with data to send to AEAT WS for invoice types:
        out_invoice and out_refund.

        :param cancel: It indicates if the dictionary if for sending a
          cancellation of the invoice.
        :return: invoices (dict) : Dict XML with data for this invoice.
        """

        invoice_date = self._change_date_format(cr, uid, invoice.date_invoice)
        company = invoice.company_id
        ejercicio = invoice.period_id.fiscalyear_id.date_start[0:4]
        periodo = invoice.period_id.date_start[5:7]
        partner = invoice.partner_id

        inv_dict = {
            "IDFactura": {
                "IDEmisorFactura": {
                    "NIF": company.vat[2:],
                },
                # On cancelled invoices, number is not filled
                "NumSerieFacturaEmisor": (
                    invoice.number or invoice.internal_number or ''
                )[0:60],
                "FechaExpedicionFacturaEmisor": invoice_date,
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
                # "Contraparte": {
                #     "NombreRazon": invoice.partner_id.name[0:120],
                # },
                "TipoDesglose": self._get_sii_out_taxes(cr, uid, invoice),
                "ImporteTotal": invoice.amount_total * sign,
            }

            if partner.sii_simplified_invoice:
                inv_dict["FacturaExpedida"]['TipoFactura'] = 'R5' if invoice.type == 'out_refund' else 'F2'



            exp_dict = inv_dict['FacturaExpedida']
            # Uso condicional de IDOtro/NIF
            # exp_dict['Contraparte'].update(self._get_sii_identifier(cr, uid, invoice))

            if not partner.sii_simplified_invoice:
                # Simplified invoices don't have counterpart
                exp_dict["Contraparte"] = {
                    "NombreRazon": partner.name[0:120],
                }
                # Uso condicional de IDOtro/NIF
                exp_dict['Contraparte'].update(self._get_sii_identifier(cr, uid, invoice))

            if invoice.type == 'out_refund':
                exp_dict['TipoRectificativa'] = invoice.sii_refund_type
                if invoice.sii_refund_type == 'S':
                    base_rectificada = 0
                    cuota_rectificada = 0
                    for s in invoice.origin_invoices_ids:
                        base_rectificada += s.amount_untaxed
                        cuota_rectificada += s.amount_tax
                    exp_dict['ImporteRectificacion'] = {
                        'BaseRectificada': base_rectificada,
                        'CuotaRectificada': cuota_rectificada
                    }
        return inv_dict

    def _get_sii_invoice_dict_in(self, cr, uid, invoice, cancel=False):
        """Build dict with data to send to AEAT WS for invoice types:
        in_invoice and in_refund.

        :param cancel: It indicates if the dictionary if for sending a
          cancellation of the invoice.
        :return: invoices (dict) : Dict XML with data for this invoice.
        """

        invoice_date = self._change_date_format(cr, uid, invoice.date_invoice)
        reg_date = self._change_date_format(cr, uid,
            self._get_account_registration_date(cr, uid, invoice),
        )


        ejercicio = invoice.period_id.fiscalyear_id.date_start[0:4]
        periodo = invoice.period_id.date_start[5:7]
        desglose_factura, tax_amount = self._get_sii_in_taxes(cr, uid, invoice)

        inv_dict = {
            "IDFactura": {
                "IDEmisorFactura": {},
                "NumSerieFacturaEmisor": (invoice.reference or '')[0:60],
                "FechaExpedicionFacturaEmisor": invoice_date},
            "PeriodoImpositivo": {
                "Ejercicio": ejercicio,
                "Periodo": periodo
            },
        }

        # Uso condicional de IDOtro/NIF
        ident = self._get_sii_identifier(cr, uid, invoice)
        inv_dict['IDFactura']['IDEmisorFactura'].update(ident)
        if cancel:
            inv_dict['IDFactura']['IDEmisorFactura'].update(
                {'NombreRazon': invoice.partner_id.name[0:120]})

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
                "ImporteTotal": invoice.amount_total * sign,
                "CuotaDeducible": float_round(tax_amount * sign, 2),
            }



        # Uso condicional de IDOtro/NIF
        inv_dict['IDFactura']['IDEmisorFactura'].update(ident)
        inv_dict['FacturaRecibida']['Contraparte'].update(ident)
        if invoice.type == 'in_refund':
            rec_dict = inv_dict['FacturaRecibida']
            rec_dict['TipoRectificativa'] = invoice.sii_refund_type
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

    def _get_sii_invoice_dict(self, cr, uid, invoice):
        self._sii_check_exceptions(cr, uid, invoice)
        if invoice.type in ['out_invoice', 'out_refund']:
            return self._get_sii_invoice_dict_out(cr, uid, invoice, cancel=False)
        elif invoice.type in ['in_invoice', 'in_refund']:
            return self._get_sii_invoice_dict_in(cr, uid, invoice, cancel=False)
        return {}

    def _get_cancel_sii_invoice_dict(self, cr, uid, invoice):
        self._sii_check_exceptions(cr, uid, invoice)
        if invoice.type in ['out_invoice', 'out_refund']:
            return self._get_sii_invoice_dict_out(cr, uid, invoice, cancel=True)
        elif invoice.type in ['in_invoice', 'in_refund']:
            return self._get_sii_invoice_dict_in(cr, uid, invoice, cancel=True)
        return {}


    def _connect_sii(self, cr, uid, wsdl, company):

        today = datetime.today()
        config_obj = self.pool.get('l10n.es.aeat.sii')
        sii_config_ids = config_obj.search(cr, uid, [
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
                if res['EstadoEnvio'] == 'Correcto':
                    self.write(cr, uid, invoice.id, {
                                                     'sii_state': 'sent',
                                                     'sii_send_failed': False,
                                                     'sii_sent': True,
                                                     'sii_csv': res['CSV']
                                                     })
                else:
                    self.write(cr, uid, invoice.id, {
                                                     'sii_send_failed': True,
                                                     })

                self.write(cr, uid, invoice.id, {'sii_return': res})

                send_error = False
                res_line = res['RespuestaLinea'][0]
                if res_line['CodigoErrorRegistro']:
                    send_error = u"{} | {}".format(
                        unicode(res_line['CodigoErrorRegistro']),
                        unicode(res_line['DescripcionErrorRegistro'])[:60])
                self.write(cr, uid, invoice.id, {'sii_send_error': send_error})

            except Exception as fault:

                new_cr = pooler.get_db(cr.dbname).cursor()


                self.write(cr, uid, invoice.id, {
                    'sii_send_failed': True,
                    'sii_send_error': fault,
                    'sii_return': fault,
                })

                new_cr.commit()
                new_cr.close()



    def action_number(self, cr, uid, ids, context=None):
        res = super(AccountInvoice, self).action_number(cr, uid, ids, context=context)
        for invoice in self.browse(cr, uid, ids):
            if invoice.sii_enabled:
                if invoice.sii_state == 'sent':
                    self.write(cr, uid, invoice.id, {
                        'sii_state': 'sent_modified'},context)
                elif invoice.sii_state == 'cancelled':
                    self.write(cr, uid, invoice.id, {
                        'sii_state': 'cancelled_modified'},context)
                company = invoice.company_id
                if company.sii_enabled and company.sii_method == 'auto':
                    self._send_invoice_to_sii(cr, uid, [invoice.id])

        return res

    def send_sii(self, cr, uid, ids, context=None):
        for invoice in self.browse(cr, uid, ids, context):
            company = invoice.company_id
            if company.sii_enabled and invoice.sii_enabled and invoice.state in ['open',
                                                                                 'paid'] and invoice.sii_state in [
                'not_sent', 'sent_modified', 'cancelled_modified']:
                self._send_invoice_to_sii(cr, uid, [invoice.id])
        return True



    def _cancel_invoice_to_sii(self, cr, uid, ids):
        for invoice in self.pool.get('account.invoice').browse(cr, uid, ids):
            company = invoice.company_id
            port_name = ''
            wsdl = ''
            if invoice.type in ['out_invoice', 'out_refund']:
                wsdl = self.pool['ir.config_parameter'].get_param(cr, uid,
                                                           'l10n_es_aeat_sii.wsdl_out', False)
                port_name = 'SuministroFactEmitidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            elif invoice.type in ['in_invoice', 'in_refund']:
                wsdl = self.pool['ir.config_parameter'].get_param(cr, uid,
                                                           'l10n_es_aeat_sii.wsdl_in', False)
                port_name = 'SuministroFactRecibidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            client = self._connect_sii(cr, uid, wsdl, company)
            serv = client.bind('siiService', port_name)
            header = self._get_sii_header(cr, uid, invoice.id, company, cancellation=True)
            try:
                inv_dict = self._get_sii_invoice_dict(cr, uid, invoice)
                if invoice.type in ['out_invoice', 'out_refund']:
                    res = serv.AnulacionLRFacturasEmitidas(
                        header, inv_dict)
                elif invoice.type in ['in_invoice', 'in_refund']:
                    res = serv.AnulacionLRFacturasRecibidas(
                        header, inv_dict)
                if res['EstadoEnvio'] == 'Correcto':
                    self.write(cr, uid, invoice.id, {
                        'sii_state': 'cancelled',
                        'sii_send_failed': False,
                        'sii_sent': True,
                        'sii_csv': res['CSV']
                    })
                else:
                    self.write(cr, uid, invoice.id, {
                        'sii_send_failed': True,
                    })

                self.write(cr, uid, invoice.id, {'sii_return': res})

                send_error = False
                res_line = res['RespuestaLinea'][0]
                if res_line['CodigoErrorRegistro']:
                    send_error = u"{} | {}".format(
                        unicode(res_line['CodigoErrorRegistro']),
                        unicode(res_line['DescripcionErrorRegistro'])[:60])
                self.write(cr, uid, invoice.id, {'sii_send_error': send_error})

            except Exception as fault:
                new_cr = pooler.get_db(cr.dbname).cursor()

                self.write(cr, uid, invoice.id, {
                    'sii_send_failed': True,
                    'sii_send_error': fault,
                    'sii_return': fault,
                })
                new_cr.commit()
                new_cr.close()

    def cancel_sii(self, cr, uid, ids, context=None):
        for invoice in self.browse(cr, uid, ids, context):
            company = invoice.company_id
            if company.sii_enabled and invoice.sii_enabled and invoice.state in ['cancel'] and invoice.sii_state in ['sent', 'sent_modified']:
                self._cancel_invoice_to_sii(cr, uid, [invoice.id])
        return True


    def action_cancel(self, cr, uid , ids, context=None):
        for invoice in self.browse(cr, uid, ids, context):
            res = super(AccountInvoice, self).action_cancel(cr, uid, ids)
            if invoice.sii_state == 'sent':
                self.write(cr, uid, invoice.id, {
                    'sii_state': 'sent_modified'})
            elif invoice.sii_state == 'cancelled_modified':
                # Case when repoen a cancelled invoice, validate and cancel again
                # without any SII communication.
                self.write(cr, uid, invoice.id, {
                    'sii_state': 'cancelled'})

        return res

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
        if invoice.partner_id.vat:
            vat = ''.join(
                e for e in invoice.partner_id.vat if e.isalnum()
            ).upper()
        else:
            vat = 'NO_DISPONIBLE'
        country_code = (
            (invoice.partner_id.vat or '')[:2]
        ).upper()
        if gen_type == 1:
            if '1117' in (invoice.sii_send_error or ''):
                return {
                    "IDOtro": {
                        "CodigoPais": country_code,
                        "IDType": '07',
                        "ID": vat[2:],
                    }
                }
            else:
                if country_code != 'ES':
                    id_type = '06' if vat == 'NO_DISPONIBLE' else '04'
                    return {
                        "IDOtro": {
                            "CodigoPais": country_code,
                            "IDType": id_type,
                            "ID": vat,
                        },
                    }
                else:
                    return {"NIF": vat[2:]}
        elif gen_type == 2:
            return {
                "IDOtro": {
                    "IDType": '02',
                    "ID": vat,
                }
            }
        elif gen_type == 3:
            if country_code != 'ES':
                id_type = '06' if vat == 'NO_DISPONIBLE' else '04'
            else:
                id_type = '06'
            return {
                "IDOtro": {
                    "CodigoPais": country_code,
                    "IDType": id_type,
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
        elif invoice.fiscal_position and \
                        invoice.fiscal_position.sii_exempt_cause != 'none':
            return invoice.fiscal_position.sii_exempt_cause


    def _get_no_taxable_cause(self, cr, uid, invoice):
        return invoice.fiscal_position.sii_no_taxable_cause or \
            'ImportePorArticulos7_14_Otros'

    def is_sii_invoice(self, cr, uid, invoice):
        """Hook method to be overridden in additional modules to verify
        if the invoice must be sended trough SII system, for special cases.

        :param self: Single invoice record
        :return: bool value indicating if the invoice should be sent to SII.
        """
        return True



    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None,
                        description=None, journal_id=None, context=None):
        res = super(AccountInvoice, self)._prepare_refund(
            cr, uid, invoice, date=date, period_id=period_id,
            description=description, journal_id=journal_id,
        )
        sii_refund_type = context.get('sii_refund_type')
        if sii_refund_type:
            res['sii_refund_type'] = sii_refund_type
        return res



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
                                                  ['RE'], invoice)
        for tax in line.invoice_line_tax_id:
            if tax in taxes_re:
                price = self._get_sii_line_price_subtotal(cr, uid, line)
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

        if tax_line.child_depend:
            tax_type = tax_line.child_ids.filtered('amount')[:1].amount
        else:
            tax_type = tax_line.amount
        if tax_type not in tax_dict:
            tax_dict[tax_type] = {
                'TipoImpositivo': str(tax_type * 100),
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
                                                         self._get_sii_line_price_subtotal(cr, uid, line),
                                                         line.quantity,
                                                         line.product_id, line.invoice_id.partner_id,
                                                         )
        tax_dict[tax_type]['BaseImponible'] += taxes['total']
        if line.invoice_id.type in ['out_invoice', 'out_refund']:
            key = 'CuotaRepercutida'
        else:
            key = 'CuotaSoportada'
        tax_dict[tax_type][key] += taxes['taxes'][0]['amount']
