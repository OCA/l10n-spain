# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Studio73 - Pablo Fuentes <pablo@studio73>
# Copyright 2017 Studio73 - Jordi Tolsà <jordi@studio73.es>
# Copyright 2017 Otherway - Pedro Rodríguez Gil
# Copyright 2017 Tecnativa - Pedro M. Baeza
# Copyright 2017 Comunitea - Omar Castiñeira <omar@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from datetime import date
from requests import Session

from openerp import _, api, exceptions, fields, models, SUPERUSER_ID
from openerp.modules.registry import RegistryManager
from openerp.tools.float_utils import float_round

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

SII_STATES = [
    ('not_sent', 'Not sent'),
    ('sent', 'Sent'),
    ('sent_modified', 'Registered in SII but last modifications not sent'),
    ('cancelled', 'Cancelled'),
    ('cancelled_modified', 'Cancelled in SII but last modifications not sent'),
]

SII_VERSION = '1.0'
SII_START_DATE = '2017-07-01'


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _default_sii_refund_type(self):
        inv_type = self.env.context.get('type')
        return 'S' if inv_type in ['out_refund', 'in_refund'] else False

    def _default_sii_registration_key(self):
        sii_key_obj = self.env['aeat.sii.mapping.registration.keys']
        type = self.env.context.get('type')
        if type in ['in_invoice', 'in_refund']:
            key = sii_key_obj.search(
                [('code', '=', '01'), ('type', '=', 'purchase')], limit=1)
        else:
            key = sii_key_obj.search(
                [('code', '=', '01'), ('type', '=', 'sale')], limit=1)
        return key

    sii_manual_description = fields.Text(
        string='SII manual description', size=500, copy=False,
    )
    sii_description_method = fields.Selection(
        related='company_id.sii_description_method', readonly=True,
    )
    sii_description = fields.Text(
        string='SII computed description', compute="_compute_sii_description",
        store=True, inverse='_inverse_sii_description',
    )
    sii_state = fields.Selection(
        selection=SII_STATES, string="SII send state", default='not_sent',
        help="Indicates the state of this invoice in relation with the "
             "presentation at the SII",
        copy=False,
    )
    sii_csv = fields.Char(string='SII CSV', copy=False, readonly=True)
    sii_return = fields.Text(string='SII Return', copy=False, readonly=True)
    sii_send_error = fields.Text(
        string='SII Send Error', readonly=True, copy=False,
    )
    sii_send_failed = fields.Boolean(
        string="SII send failed", copy=False,
        help="Indicates that the last attempt to communicate this invoice to "
             "the SII has failed. See SII return for details",
    )
    sii_refund_type = fields.Selection(
        selection=[('S', 'By substitution'), ('I', 'By differences')],
        string="SII Refund Type", default=_default_sii_refund_type,
        oldname='refund_type',
    )
    sii_registration_key = fields.Many2one(
        comodel_name='aeat.sii.mapping.registration.keys',
        string="SII registration key", default=_default_sii_registration_key,
        oldname='registration_key',
        # required=True, This is not set as required here to avoid the
        # set not null constraint warning
    )
    sii_enabled = fields.Boolean(
        string='Enable SII', compute='_compute_sii_enabled',
    )
    invoice_jobs_ids = fields.Many2many(
        comodel_name='queue.job', column1='invoice_id', column2='job_id',
        string="Connector Jobs",
    )

    @api.onchange('sii_refund_type')
    def onchange_sii_refund_type(self):
        if (self.sii_enabled and self.sii_refund_type == 'S' and
                not self.origin_invoices_ids):
            self.sii_refund_type = False
            return {
                'warning': {
                    'message': _(
                        'You must have at least one refunded invoice'
                    ),
                }
            }

    @api.onchange('fiscal_position')
    def onchange_fiscal_position_l10n_es_aeat_sii(self):
        for invoice in self.filtered('fiscal_position'):
            if 'out' in invoice.type:
                key = invoice.fiscal_position.sii_registration_key_sale
            else:
                key = invoice.fiscal_position.sii_registration_key_purchase
            invoice.sii_registration_key = key

    @api.model
    def create(self, vals):
        """Complete registration key for auto-generated invoices."""
        invoice = super(AccountInvoice, self).create(vals)
        if vals.get('fiscal_position') and \
                not vals.get('sii_registration_key'):
            invoice.onchange_fiscal_position_l10n_es_aeat_sii()
        return invoice

    @api.multi
    def write(self, vals):
        """For supplier invoices the SII primary key is the supplier
        VAT/ID Otro and the supplier invoice number. Cannot let change these
        values in a SII registered supplier invoice"""
        for invoice in self:
            if invoice.sii_state == 'not_sent':
                continue
            if 'date_invoice' in vals:
                raise exceptions.Warning(
                    _("You cannot change the invoice date of an invoice "
                      "already registered at the SII. You must cancel the "
                      "invoice and create a new one with the correct date")
                )
            if (invoice.type in ['in_invoice', 'in refund']):
                if 'partner_id' in vals:
                    correct_partners = invoice.partner_id.commercial_partner_id
                    correct_partners |= correct_partners.child_ids
                    if vals['partner_id'] not in correct_partners.ids:
                        raise exceptions.Warning(
                            _("You cannot change the supplier of an invoice "
                              "already registered at the SII. You must cancel "
                              "the invoice and create a new one with the "
                              "correct supplier")
                            )
                elif 'supplier_invoice_number' in vals:
                    raise exceptions.Warning(
                        _("You cannot change the supplier invoice number of "
                          "an invoice already registered at the SII. You must "
                          "cancel the invoice and create a new one with the "
                          "correct number")
                    )
        res = super(AccountInvoice, self).write(vals)
        if vals.get('fiscal_position') and \
                not vals.get('sii_registration_key'):
            self.onchange_fiscal_position_l10n_es_aeat_sii()
        return res

    @api.multi
    def unlink(self):
        """A registered invoice at the SII cannot be deleted"""
        for invoice in self:
            if invoice.sii_state != 'not_sent':
                raise exceptions.Warning(
                    _("You cannot delete an invoice already registered at the "
                      "SII.")
                )
        return super(AccountInvoice, self).unlink()

    @api.multi
    def map_sii_tax_template(self, tax_template, mapping_taxes):
        """Adds a tax template -> tax id to the mapping.
        Adapted from account_chart_update module.

        :param self: Single invoice record.
        :param tax_template: Tax template record.
        :param mapping_taxes: Dictionary with all the tax templates mapping.
        :return: Tax template current mapping
        """
        self.ensure_one()
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
            criteria = ['|'] + criteria
            criteria += [
                '|',
                ('description', '=', tax_template.description),
                ('name', '=', tax_template.description),
            ]
        criteria += [('company_id', '=', self.company_id.id)]
        mapping_taxes[tax_template] = tax_obj.search(criteria)
        return mapping_taxes[tax_template]

    @api.multi
    def _get_sii_taxes_map(self, codes):
        """Return the codes that correspond to that sii map line codes.

        :param self: Single invoice record.
        :param codes: List of code strings to get the mapping.
        :return: Recordset with the corresponding codes
        """
        self.ensure_one()
        taxes = self.env['account.tax']
        sii_map = self.env['aeat.sii.map'].search(
            ['|',
             ('date_from', '<=', self.date_invoice),
             ('date_from', '=', False),
             '|',
             ('date_to', '>=', self.date_invoice),
             ('date_to', '=', False)], limit=1)
        mapping_taxes = {}
        tax_templates = sii_map.sudo().map_lines.filtered(
            lambda x: x.code in codes
        ).taxes
        for tax_template in tax_templates:
            taxes += self.map_sii_tax_template(tax_template, mapping_taxes)
        return taxes

    @api.multi
    def _change_date_format(self, date):
        datetimeobject = fields.Date.from_string(date)
        new_date = datetimeobject.strftime('%d-%m-%Y')
        return new_date

    @api.multi
    def _get_sii_header(self, tipo_comunicacion=False, cancellation=False):
        """Builds SII send header

        :param tipo_comunicacion String 'A0': new reg, 'A1': modification
        :param cancellation Bool True when the communitacion es for invoice
            cancellation
        :return Dict with header data depending on cancellation
        """
        self.ensure_one()
        company = self.company_id
        if not company.vat:
            raise exceptions.Warning(_(
                "No VAT configured for the company '{}'").format(company.name))
        header = {
            "IDVersionSii": SII_VERSION,
            "Titular": {
                "NombreRazon": self.company_id.name[0:120],
                "NIF": self.company_id.vat[2:]}
        }
        if not cancellation:
            header.update({"TipoComunicacion": tipo_comunicacion})
        return header

    @api.multi
    def _get_sii_out_taxes(self):
        """Get the taxes for sales invoices.

        :param self: Single invoice record.
        """
        self.ensure_one()
        taxes_dict = {}
        taxes_f = {}
        taxes_to = {}
        tax_breakdown = {}
        taxes_sfesb = self._get_sii_taxes_map(['SFESB'])
        taxes_sfesbe = self._get_sii_taxes_map(['SFESBE'])
        taxes_sfesisp = self._get_sii_taxes_map(['SFESISP'])
        # taxes_sfesisps = self._get_taxes_map(['SFESISPS'])
        taxes_sfens = self._get_sii_taxes_map(['SFENS'])
        taxes_sfess = self._get_sii_taxes_map(['SFESS'])
        taxes_sfesse = self._get_sii_taxes_map(['SFESSE'])
        default_no_taxable_cause = self._get_no_taxable_cause()
        # Check if refund type is 'By differences'. Negative amounts!
        sign = self._get_sii_sign()
        for inv_line in self.invoice_line:
            exempt_cause = self._get_sii_exempt_cause(inv_line.product_id)
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
                            inv_line._get_sii_line_price_subtotal() * sign
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
                        not_ex_type = sub_dict['NoExenta']['TipoNoExenta']
                        if tax_line in taxes_sfesisp:
                            is_s3 = not_ex_type == 'S1'
                        else:
                            is_s3 = not_ex_type == 'S2'
                        if is_s3:
                            sub_dict['NoExenta']['TipoNoExenta'] = 'S3'
                        inv_line._update_sii_tax_line(taxes_f, tax_line)
                # No sujetas
                if tax_line in taxes_sfens:
                    nsub_dict = tax_breakdown.setdefault(
                        'NoSujeta', {default_no_taxable_cause: 0},
                    )
                    nsub_dict[default_no_taxable_cause] += inv_line.\
                        _get_sii_line_price_subtotal()
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
                        exempt_dict['BaseImponible'] += inv_line.\
                            _get_sii_line_price_subtotal() * sign
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
                        inv_line._update_sii_tax_line(taxes_to, tax_line)
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
        if 'Sujeta' in tax_breakdown and 'Exenta' in tax_breakdown['Sujeta']:
            exempt_dict = tax_breakdown['Sujeta']['Exenta']
            exempt_dict['BaseImponible'] = \
                float_round(exempt_dict['BaseImponible'], 2)
        # Ajustes finales breakdown
        # - DesgloseFactura y DesgloseTipoOperacion son excluyentes
        # - Ciertos condicionantes obligan DesgloseTipoOperacion
        country_code = (
            self.partner_id.commercial_partner_id.country_id.code or
            (self.partner_id.vat or '')[:2]
        ).upper()
        if (('DesgloseTipoOperacion' in taxes_dict and
                'DesgloseFactura' in taxes_dict) or
                ('DesgloseFactura' in taxes_dict and
                 self._get_sii_gen_type() in (2, 3)) or
                ('DesgloseFactura' in taxes_dict and
                 self._get_sii_gen_type() == 1 and country_code != 'ES')):
            taxes_dict.setdefault('DesgloseTipoOperacion', {})
            taxes_dict['DesgloseTipoOperacion']['Entrega'] = \
                taxes_dict['DesgloseFactura']
            del taxes_dict['DesgloseFactura']
        return taxes_dict

    @api.multi
    def _get_sii_in_taxes(self):
        """Get the taxes for purchase invoices.

        :param self:  Single invoice record.
        """
        self.ensure_one()
        taxes_dict = {}
        taxes_f = {}
        taxes_isp = {}
        taxes_sfrs = self._get_sii_taxes_map(['SFRS'])
        taxes_sfrisp = self._get_sii_taxes_map(['SFRISP'])
        taxes_sfrns = self._get_sii_taxes_map(['SFRNS'])
        tax_amount = 0.0
        # Check if refund type is 'By differences'. Negative amounts!
        sign = self._get_sii_sign()
        for inv_line in self.invoice_line:
            for tax_line in inv_line.invoice_line_tax_id:
                if tax_line in taxes_sfrisp:
                    inv_line._update_sii_tax_line(taxes_isp, tax_line)
                elif tax_line in taxes_sfrs:
                    inv_line._update_sii_tax_line(taxes_f, tax_line)
                elif tax_line in taxes_sfrns:
                    nsub_dict = taxes_dict.setdefault(
                        'DesgloseIVA',
                        {'DetalleIVA': {'BaseImponible': 0}},
                    )
                    nsub_dict['DetalleIVA']['BaseImponible'] += inv_line.\
                        _get_sii_line_price_subtotal() * sign

        if taxes_isp:
            taxes_dict.setdefault(
                'InversionSujetoPasivo', {'DetalleIVA': taxes_isp.values()},
            )
        if taxes_f:
            taxes_dict.setdefault(
                'DesgloseIVA', {'DetalleIVA': taxes_f.values()},
            )
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

    @api.multi
    def _sii_check_exceptions(self):
        """Inheritable method for exceptions control when sending SII invoices.
        """
        self.ensure_one()
        gen_type = self._get_sii_gen_type()
        partner = self.partner_id.commercial_partner_id
        country_code = (
            partner.country_id.code or (self.partner_id.vat or '')[:2]
        ).upper()
        if partner.sii_simplified_invoice and self.type[:2] == 'in':
            raise exceptions.Warning(
                _("You can't make a supplier simplified invoice.")
            )
        if ((gen_type != 3 or country_code == 'ES') and
                not partner.vat and not partner.sii_simplified_invoice):
            raise exceptions.Warning(
                _("The partner has not a VAT configured.")
            )
        if not self.company_id.chart_template_id:
            raise exceptions.Warning(_(
                'You have to select what account chart template use this'
                ' company.'))
        if not self.company_id.sii_enabled:
            raise exceptions.Warning(
                _("This company doesn't have SII enabled.")
            )
        if not self.sii_enabled:
            raise exceptions.Warning(
                _("This invoice is not SII enabled.")
            )
        if not self.supplier_invoice_number\
                and self.type in ['in_invoice', 'in_refund']:
            raise exceptions.Warning(
                _("The supplier number invoice is required")
            )

    @api.multi
    def _get_account_registration_date(self):
        """Hook method to allow the setting of the account registration date
        of each supplier invoice. The SII recommends to set the send date as
        the default value (point 9.3 of the document
        SII_Descripcion_ServicioWeb_v0.7.pdf), so by default we return
        the current date
        :return String date in the format %Y-%m-%d"""
        return date.today().strftime("%Y-%m-%d")

    @api.multi
    def _get_sii_invoice_dict_out(self, cancel=False):
        """Build dict with data to send to AEAT WS for invoice types:
        out_invoice and out_refund.

        :param cancel: It indicates if the dictionary is for sending a
          cancellation of the invoice.
        :return: invoices (dict) : Dict XML with data for this invoice.
        """
        self.ensure_one()
        invoice_date = self._change_date_format(self.date_invoice)
        partner = self.partner_id.commercial_partner_id
        company = self.company_id
        ejercicio = fields.Date.from_string(
            self.period_id.fiscalyear_id.date_start).year
        periodo = '%02d' % fields.Date.from_string(
            self.period_id.date_start).month
        inv_dict = {
            "IDFactura": {
                "IDEmisorFactura": {
                    "NIF": company.vat[2:],
                },
                # On cancelled invoices, number is not filled
                "NumSerieFacturaEmisor": (
                    self.number or self.internal_number or ''
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
            sign = self._get_sii_sign()
            if partner.sii_simplified_invoice:
                tipo_factura = 'R5' if self.type == 'out_refund' else 'F2'
            else:
                tipo_factura = 'R4' if self.type == 'out_refund' else 'F1'
            inv_dict["FacturaExpedida"] = {
                "TipoFactura": tipo_factura,
                "ClaveRegimenEspecialOTrascendencia": (
                    self.sii_registration_key.code
                ),
                "DescripcionOperacion": self.sii_description,
                "TipoDesglose": self._get_sii_out_taxes(),
                "ImporteTotal": self.cc_amount_total * sign,
            }
            exp_dict = inv_dict['FacturaExpedida']
            if not partner.sii_simplified_invoice:
                # Simplified invoices don't have counterpart
                exp_dict["Contraparte"] = {
                    "NombreRazon": partner.name[0:120],
                }
                # Uso condicional de IDOtro/NIF
                exp_dict['Contraparte'].update(self._get_sii_identifier())
            if self.type == 'out_refund':
                exp_dict['TipoRectificativa'] = self.sii_refund_type
                if self.sii_refund_type == 'S':
                    exp_dict['ImporteRectificacion'] = {
                        'BaseRectificada': sum(
                            self.
                            mapped('origin_invoices_ids.cc_amount_untaxed')
                        ),
                        'CuotaRectificada': sum(
                            self.mapped('origin_invoices_ids.cc_amount_tax')
                        ),
                    }
        return inv_dict

    @api.multi
    def _get_sii_invoice_dict_in(self, cancel=False):
        """Build dict with data to send to AEAT WS for invoice types:
        in_invoice and in_refund.

        :param cancel: It indicates if the dictionary if for sending a
          cancellation of the invoice.
        :return: invoices (dict) : Dict XML with data for this invoice.
        """
        self.ensure_one()
        invoice_date = self._change_date_format(self.date_invoice)
        reg_date = self._change_date_format(
            self._get_account_registration_date(),
        )
        ejercicio = fields.Date.from_string(
            self.period_id.fiscalyear_id.date_start).year
        periodo = '%02d' % fields.Date.from_string(
            self.period_id.date_start).month
        desglose_factura, tax_amount = self._get_sii_in_taxes()
        inv_dict = {
            "IDFactura": {
                "IDEmisorFactura": {},
                "NumSerieFacturaEmisor": (
                    (self.supplier_invoice_number or '')[:60]
                ),
                "FechaExpedicionFacturaEmisor": invoice_date},
            "PeriodoImpositivo": {
                "Ejercicio": ejercicio,
                "Periodo": periodo
            },
        }
        # Uso condicional de IDOtro/NIF
        ident = self._get_sii_identifier()
        inv_dict['IDFactura']['IDEmisorFactura'].update(ident)
        if cancel:
            inv_dict['IDFactura']['IDEmisorFactura'].update(
                {'NombreRazon': (
                    self.partner_id.commercial_partner_id.name[0:120]
                    )}
            )
        else:
            # Check if refund type is 'By differences'. Negative amounts!
            sign = self._get_sii_sign()
            inv_dict["FacturaRecibida"] = {
                # TODO: Incluir los 5 tipos de facturas rectificativas
                "TipoFactura": (
                    'R4' if self.type == 'in_refund' else 'F1'
                ),
                "ClaveRegimenEspecialOTrascendencia": (
                    self.sii_registration_key.code
                ),
                "DescripcionOperacion": self.sii_description,
                "DesgloseFactura": desglose_factura,
                "Contraparte": {
                    "NombreRazon": (
                        self.partner_id.commercial_partner_id.name[0:120]
                    )
                },
                "FechaRegContable": reg_date,
                "ImporteTotal": self.cc_amount_total * sign,
                "CuotaDeducible": float_round(tax_amount * sign, 2),
            }
            # Uso condicional de IDOtro/NIF
            inv_dict['FacturaRecibida']['Contraparte'].update(ident)
            if self.type == 'in_refund':
                rec_dict = inv_dict['FacturaRecibida']
                rec_dict['TipoRectificativa'] = self.sii_refund_type
                refund_tax_amount = sum([
                    x._get_sii_in_taxes()[1]
                    for x in self.origin_invoices_ids
                ])
                if self.sii_refund_type == 'S':
                    rec_dict['ImporteRectificacion'] = {
                        'BaseRectificada': sum(
                            self.
                            mapped('origin_invoices_ids.cc_amount_untaxed')
                        ),
                        'CuotaRectificada': refund_tax_amount,
                    }
        return inv_dict

    @api.multi
    def _get_sii_invoice_dict(self):
        self.ensure_one()
        self._sii_check_exceptions()
        if self.type in ['out_invoice', 'out_refund']:
            return self._get_sii_invoice_dict_out()
        elif self.type in ['in_invoice', 'in_refund']:
            return self._get_sii_invoice_dict_in()
        return {}

    @api.multi
    def _get_cancel_sii_invoice_dict(self):
        self.ensure_one()
        self._sii_check_exceptions()
        if self.type in ['out_invoice', 'out_refund']:
            return self._get_sii_invoice_dict_out(cancel=True)
        elif self.type in ['in_invoice', 'in_refund']:
            return self._get_sii_invoice_dict_in(cancel=True)
        return {}

    @api.multi
    def _connect_sii(self, wsdl):
        today = fields.Date.today()
        sii_config = self.env['l10n.es.aeat.sii'].search([
            ('company_id', '=', self.company_id.id),
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
    def _process_invoice_for_sii_send(self):
        """Process invoices for sending to the SII. Adds general checks from
        configuration parameters and invoice availability for SII. If the
        invoice is to be sent the decides the send method: direct send or
        via connector depending on 'Use connector' configuration"""
        # De momento evitamos enviar facturas del primer semestre si no estamos
        # en entorno de pruebas
        invoices = self.filtered(
            lambda i: (
                i.company_id.sii_test or
                i.period_id.date_start >= SII_START_DATE
            )
        )
        queue_obj = self.env['queue.job'].sudo()
        for invoice in invoices:
            company = invoice.company_id
            if not company.use_connector:
                invoice._send_invoice_to_sii()
            else:
                eta = company._get_sii_eta()
                session = ConnectorSession(
                    self.env.cr, SUPERUSER_ID, context=self.env.context,
                )
                new_delay = confirm_one_invoice.delay(
                    session, 'account.invoice', invoice.id,
                    eta=eta if not invoice.sii_send_failed else False,
                )
                invoice.sudo().invoice_jobs_ids |= queue_obj.search(
                    [('uuid', '=', new_delay)], limit=1,
                )

    @api.multi
    def _send_invoice_to_sii(self):
        for invoice in self.filtered(lambda i: i.state in ['open', 'paid']):
            company = invoice.company_id
            port_name = ''
            wsdl = ''
            if invoice.type in ['out_invoice', 'out_refund']:
                wsdl = self.env['ir.config_parameter'].get_param(
                    'l10n_es_aeat_sii.wsdl_out', False)
                port_name = 'SuministroFactEmitidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            elif invoice.type in ['in_invoice', 'in_refund']:
                wsdl = self.env['ir.config_parameter'].get_param(
                    'l10n_es_aeat_sii.wsdl_in', False)
                port_name = 'SuministroFactRecibidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            client = self._connect_sii(wsdl)
            serv = client.bind('siiService', port_name)
            if invoice.sii_state == 'not_sent':
                tipo_comunicacion = 'A0'
            else:
                tipo_comunicacion = 'A1'
            header = invoice._get_sii_header(tipo_comunicacion)
            try:
                inv_dict = invoice._get_sii_invoice_dict()
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
                    invoice.sii_state = 'sent'
                    invoice.sii_csv = res['CSV']
                    invoice.sii_send_failed = False
                else:
                    invoice.sii_send_failed = True
                invoice.sii_return = res
                send_error = False
                res_line = res['RespuestaLinea'][0]
                if res_line['CodigoErrorRegistro']:
                    send_error = u"{} | {}".format(
                        unicode(res_line['CodigoErrorRegistro']),
                        unicode(res_line['DescripcionErrorRegistro'])[:60])
                invoice.sii_send_error = send_error
            except Exception as fault:
                new_cr = RegistryManager.get(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                invoice = env['account.invoice'].browse(self.id)
                invoice.sii_send_failed = True
                invoice.sii_send_error = fault
                invoice.sii_return = fault
                new_cr.commit()
                new_cr.close()
                raise

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for invoice in self.filtered('sii_enabled'):
            if invoice.sii_state == 'sent':
                invoice.sii_state = 'sent_modified'
            elif invoice.sii_state == 'cancelled':
                invoice.sii_state = 'cancelled_modified'
            company = invoice.company_id
            if company.sii_method != 'auto':
                continue
            invoice._process_invoice_for_sii_send()
        return res

    @api.multi
    def send_sii(self):
        invoices = self.filtered(
            lambda i: (
                i.sii_enabled and i.state in ['open', 'paid'] and
                i.sii_state in [
                    'not_sent', 'sent_modified', 'cancelled_modified',
                ]
            )
        )
        if not invoices._cancel_invoice_jobs():
            raise exceptions.Warning(_(
                'You can not communicate this invoice at this moment '
                'because there is a job running!'))
        invoices._process_invoice_for_sii_send()

    @api.multi
    def _cancel_invoice_to_sii(self):
        for invoice in self.filtered(lambda i: i.state in ['cancel']):
            company = invoice.company_id
            port_name = ''
            wsdl = ''
            if invoice.type in ['out_invoice', 'out_refund']:
                wsdl = self.env['ir.config_parameter'].get_param(
                    'l10n_es_aeat_sii.wsdl_out', False)
                port_name = 'SuministroFactEmitidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            elif invoice.type in ['in_invoice', 'in_refund']:
                wsdl = self.env['ir.config_parameter'].get_param(
                    'l10n_es_aeat_sii.wsdl_in', False)
                port_name = 'SuministroFactRecibidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            client = self._connect_sii(wsdl)
            serv = client.bind('siiService', port_name)
            header = invoice._get_sii_header(cancellation=True)
            try:
                inv_dict = invoice._get_cancel_sii_invoice_dict()
                if invoice.type in ['out_invoice', 'out_refund']:
                    res = serv.AnulacionLRFacturasEmitidas(
                        header, inv_dict)
                elif invoice.type in ['in_invoice', 'in_refund']:
                    res = serv.AnulacionLRFacturasRecibidas(
                        header, inv_dict)
                # TODO Facturas intracomunitarias 66 RIVA
                # elif invoice.fiscal_position.id == self.env.ref(
                #     'account.fp_intra').id:
                #     res = serv.AnulacionLRDetOperacionIntracomunitaria(
                #         header, invoices)
                if res['EstadoEnvio'] == 'Correcto':
                    invoice.sii_state = 'cancelled'
                    invoice.sii_csv = res['CSV']
                    invoice.sii_send_failed = False
                else:
                    invoice.sii_send_failed = True
                invoice.sii_return = res
                send_error = False
                res_line = res['RespuestaLinea'][0]
                if res_line['CodigoErrorRegistro']:
                    send_error = u"{} | {}".format(
                        unicode(res_line['CodigoErrorRegistro']),
                        unicode(res_line['DescripcionErrorRegistro'])[:60])
                invoice.sii_send_error = send_error
            except Exception as fault:
                new_cr = RegistryManager.get(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                invoice = env['account.invoice'].browse(self.id)
                invoice.sii_send_error = fault
                invoice.sii_send_failed = True
                invoice.sii_return = fault
                new_cr.commit()
                new_cr.close()
                raise

    @api.multi
    def cancel_sii(self):
        invoices = self.filtered(
            lambda i: (i.sii_enabled and i.state in ['cancel'] and
                       i.sii_state in ['sent', 'sent_modified'])
        )
        if not invoices._cancel_invoice_jobs():
            raise exceptions.Warning(_(
                'You can not communicate the cancellation of this invoice '
                'at this moment because there is a job running!'))
        queue_obj = self.env['queue.job']
        for invoice in invoices:
            company = invoice.company_id
            if not company.use_connector:
                invoice._cancel_invoice_to_sii()
            else:
                eta = company._get_sii_eta()
                session = ConnectorSession.from_env(self.env)
                new_delay = cancel_one_invoice.delay(
                    session, 'account.invoice', invoice.id, eta=eta)
                queue_ids = queue_obj.search([
                    ('uuid', '=', new_delay)
                ], limit=1)
                invoice.sudo().invoice_jobs_ids |= queue_ids

    @api.multi
    def _cancel_invoice_jobs(self):
        for queue in self.mapped('invoice_jobs_ids'):
            if queue.state == 'started':
                return False
            elif queue.state in ('pending', 'enqueued', 'failed'):
                queue.sudo().unlink()
        return True

    @api.multi
    def action_cancel(self):
        if not self._cancel_invoice_jobs():
            raise exceptions.Warning(_(
                'You can not cancel this invoice because'
                ' there is a job running!'))
        res = super(AccountInvoice, self).action_cancel()
        if self.sii_state == 'sent':
            self.sii_state = 'sent_modified'
        elif self.sii_state == 'cancelled_modified':
            # Case when repoen a cancelled invoice, validate and cancel again
            # without any SII communication.
            self.sii_state = 'cancelled'
        return res

    @api.multi
    def action_cancel_draft(self):
        if not self._cancel_invoice_jobs():
            raise exceptions.Warning(_(
                'You can not set to draft this invoice because'
                ' there is a job running!'))
        return super(AccountInvoice, self).action_cancel_draft()

    @api.multi
    def _get_sii_gen_type(self):
        """Make a choice for general invoice type

        Returns:
            int: 1 (National), 2 (Intracom), 3 (Export)
        """
        self.ensure_one()
        partner_ident = self.fiscal_position.sii_partner_identification_type
        if partner_ident:
            res = int(partner_ident)
        elif self.fiscal_position.name == u'Régimen Intracomunitario':
            res = 2
        elif (self.fiscal_position.name ==
              u'Régimen Extracomunitario / Canarias, Ceuta y Melilla'):
            res = 3
        else:
            res = 1
        return res

    @api.multi
    def _get_sii_identifier(self):
        """Get the SII structure for a partner identifier depending on the
        conditions of the invoice.
        """
        self.ensure_one()
        gen_type = self._get_sii_gen_type()
        # Limpiar alfanum
        if self.partner_id.vat:
            vat = ''.join(
                e for e in self.partner_id.vat if e.isalnum()
            ).upper()
        else:
            vat = 'NO_DISPONIBLE'
        country_code = (
            self.partner_id.commercial_partner_id.country_id.code or
            (self.partner_id.vat or '')[:2]
        ).upper()
        if gen_type == 1:
            if '1117' in (self.sii_send_error or ''):
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
        elif gen_type == 3 and country_code != 'ES':
            id_type = '06' if vat == 'NO_DISPONIBLE' else '04'
            return {
                "IDOtro": {
                    "CodigoPais": country_code,
                    "IDType": id_type,
                    "ID": vat,
                },
            }
        elif gen_type == 3:
            return {"NIF": vat[2:]}

    @api.multi
    def _get_sii_exempt_cause(self, product):
        """Código de la causa de exención según 3.6 y 3.7 de la FAQ del SII."""
        self.ensure_one()
        gen_type = self._get_sii_gen_type()
        if gen_type == 2:
            return 'E5'
        elif gen_type == 3:
            return 'E2'
        elif product.sii_exempt_cause != 'none':
            return product.sii_exempt_cause
        elif self.fiscal_position and \
                self.fiscal_position.sii_exempt_cause != 'none':
            return self.fiscal_position.sii_exempt_cause

    @api.multi
    def _get_no_taxable_cause(self):
        self.ensure_one()
        return self.fiscal_position.sii_no_taxable_cause or \
            'ImportePorArticulos7_14_Otros'

    def is_sii_invoice(self):
        """Hook method to be overridden in additional modules to verify
        if the invoice must be sended trough SII system, for special cases.

        :param self: Single invoice record
        :return: bool value indicating if the invoice should be sent to SII.
        """
        self.ensure_one()

    @api.multi
    @api.depends('invoice_line', 'invoice_line.name', 'company_id',
                 'sii_manual_description')
    def _compute_sii_description(self):
        for invoice in self:
            if invoice.type in ['out_invoice', 'out_refund']:
                description = invoice.company_id.sii_header_customer or ''
            else:  # supplier invoices
                description = invoice.company_id.sii_header_supplier or ''
            method = invoice.company_id.sii_description_method
            if method == 'fixed':
                description += (invoice.company_id.sii_description or '/')
            elif method == 'manual':
                description = (
                    invoice.sii_manual_description or description or '/'
                )
            else:  # auto method
                if invoice.invoice_line:
                    if description:
                        description += ' | '
                    description += ' - '.join(
                        invoice.mapped('invoice_line.name')
                    )
            invoice.sii_description = description[:500] or '/'

    @api.multi
    def _inverse_sii_description(self):
        for invoice in self:
            invoice.sii_manual_description = invoice.sii_description

    @api.multi
    @api.depends('company_id', 'company_id.sii_enabled',
                 'fiscal_position', 'fiscal_position.sii_active')
    def _compute_sii_enabled(self):
        """Compute if the invoice is enabled for the SII"""
        for invoice in self:
            if invoice.company_id.sii_enabled:
                invoice.sii_enabled = (
                    (invoice.fiscal_position and
                     invoice.fiscal_position.sii_active) or
                    not invoice.fiscal_position
                )
            else:
                invoice.sii_enabled = False

    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None,
                        description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(
            invoice, date=date, period_id=period_id,
            description=description, journal_id=journal_id,
        )
        sii_refund_type = self.env.context.get('sii_refund_type')
        supplier_invoice_number_refund = self.env.context.get(
            'supplier_invoice_number'
        )
        if sii_refund_type:
            res['sii_refund_type'] = sii_refund_type
        if supplier_invoice_number_refund:
            res['supplier_invoice_number'] = supplier_invoice_number_refund

        return res

    @api.multi
    def _get_sii_sign(self):
        self.ensure_one()
        return -1.0 if self.sii_refund_type == 'I' and 'refund' in self.type \
            else 1.0


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    def _get_sii_line_price_unit(self):
        """Obtain the effective invoice line price after discount. This is
        obtain through this method, as it can be inherited in other modules
        for altering the expected amount according other criteria."""
        self.ensure_one()
        price_unit = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        if self.invoice_id.currency_id != \
                self.invoice_id.company_id.currency_id:
            from_currency = self.invoice_id.currency_id.\
                with_context(date=self.invoice_id.date_invoice)
            price_unit = from_currency.\
                compute(price_unit, self.invoice_id.company_id.currency_id)
        return price_unit

    @api.multi
    def _get_sii_line_price_subtotal(self):
        """Obtain the effective invoice line price after discount. Needed as
        we can modify the unit price via inheritance."""
        self.ensure_one()
        return self._get_sii_line_price_unit() * self.quantity

    @api.multi
    def _get_sii_tax_line_req(self):
        """Get any possible tax amounts for 'Recargo equivalencia'."""
        self.ensure_one()
        taxes_re = self.invoice_id._get_sii_taxes_map(['RE'])
        for tax in self.invoice_line_tax_id:
            if tax in taxes_re:
                price = self._get_sii_line_price_unit()
                taxes = tax.compute_all(
                    price, self.quantity, self.product_id,
                    self.invoice_id.partner_id,
                )
                taxes['percentage'] = tax.amount
                return taxes
        return {}

    @api.model
    def _update_sii_tax_line(self, tax_dict, tax_line):
        """Update the SII taxes dictionary for the passed tax line.

        :param self: Single invoice line record.
        :param tax_dict: Previous SII taxes dictionary.
        :param tax_line: Tax line that is being analyzed.
        """
        self.ensure_one()
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
        tax_line_req = self._get_sii_tax_line_req()
        if tax_line_req:
            tipo_recargo = tax_line_req['percentage'] * 100
            cuota_recargo = tax_line_req['taxes'][0]['amount']
            tax_dict[tax_type]['TipoRecargoEquivalencia'] = tipo_recargo
            tax_dict[tax_type].setdefault('CuotaRecargoEquivalencia', 0)
            tax_dict[tax_type]['CuotaRecargoEquivalencia'] += cuota_recargo
        # Rest of the taxes
        taxes = tax_line.compute_all(
            self._get_sii_line_price_unit(), self.quantity,
            self.product_id, self.invoice_id.partner_id,
        )
        tax_dict[tax_type]['BaseImponible'] += taxes['total']
        if self.invoice_id.type in ['out_invoice', 'out_refund']:
            key = 'CuotaRepercutida'
        else:
            key = 'CuotaSoportada'
        tax_dict[tax_type][key] += taxes['taxes'][0]['amount']


@job(default_channel='root.invoice_validate_sii')
def confirm_one_invoice(session, model_name, invoice_id):
    model = session.env[model_name]
    invoice = model.browse(invoice_id)
    if invoice.exists():
        invoice._send_invoice_to_sii()


@job(default_channel='root.invoice_validate_sii')
def cancel_one_invoice(session, model_name, invoice_id):
    model = session.env[model_name]
    invoice = model.browse(invoice_id)
    if invoice.exists():
        invoice._cancel_invoice_to_sii()
