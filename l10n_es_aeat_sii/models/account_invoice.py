# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Studio73 - Pablo Fuentes <pablo@studio73>
# Copyright 2017 Studio73 - Jordi Tolsà <jordi@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import models, fields, api, _
from requests import Session

from datetime import datetime, date
from odoo.exceptions import Warning

import logging

_logger = logging.getLogger(__name__)

try:
    from zeep import Client
    from zeep.transports import Transport
    from zeep.plugins import HistoryPlugin
except (ImportError, IOError) as err:
    _logger.debug(err)

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    _logger.debug('Can not `import queue_job`.')
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial
    job = empty_decorator_factory


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _default_refund_type(self):
        inv_type = self.env.context.get('type')
        return 'S' if inv_type in ['out_refund', 'in_refund'] else False

    def _default_registration_key(self):
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
    sii_sent = fields.Boolean(string='SII Sent', copy=False)
    sii_csv = fields.Char(string='SII CSV', copy=False)
    sii_return = fields.Text(string='SII Return', copy=False)
    sii_send_error = fields.Text(string='SII Send Error')
    refund_type = fields.Selection(
        selection=[('S', 'By substitution'), ('I', 'By differences')],
        string="Refund Type", default=_default_refund_type)
    registration_key = fields.Many2one(
        comodel_name='aeat.sii.mapping.registration.keys',
        string="SII registration key", default=_default_registration_key,
        # required=True, This is not set as required here to avoid the
        # set not null constraint warning
    )
    sii_enabled = fields.Boolean(
        string='Enable SII', related='company_id.sii_enabled',
    )
    invoice_jobs_ids = fields.Many2many(
        'queue.job',
        'invoice_id',
        'job_id',
        string="Invoice Jobs")

    @api.onchange('refund_type')
    def onchange_refund_type_l10n_es_aeat_sii(self):
        if self.refund_type == 'S' and not self.origin_invoice_ids:
            self.refund_type = False
            return {
                'warning': {
                    'message': _(
                        'You must have at least one refunded invoice'
                    ),
                }
            }

    @api.onchange('fiscal_position_id')
    def onchange_fiscal_position_id_l10n_es_aeat_sii(self):
        for invoice in self.filtered('fiscal_position_id'):
            if 'out' in invoice.type:
                key = invoice.fiscal_position_id.sii_registration_key_sale
            else:
                key = invoice.fiscal_position_id.sii_registration_key_purchase
            invoice.registration_key = key

    @api.model
    def create(self, vals):
        """Complete registration key for auto-generated invoices."""
        invoice = super(AccountInvoice, self).create(vals)
        if invoice.fiscal_position_id and not invoice.registration_key:
            invoice.onchange_fiscal_position_id_l10n_es_aeat_sii()
        return invoice

    @api.multi
    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        if vals.get('fiscal_position_id'):
            self.filtered(
                lambda x: x.fiscal_position_id and not x.registration_key
            ).onchange_fiscal_position_id_l10n_es_aeat_sii()
        return res

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
            criteria = ['|', '|'] + criteria
            criteria += [('description', '=', tax_template.description),
                         ('name', '=', tax_template.description)]
        criteria += [('company_id', '=', self.company_id.id)]
        mapping_taxes[tax_template] = tax_obj.search(criteria, limit=1)
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
        sii_map_obj = self.env['aeat.sii.map']
        sii_map_line_obj = self.env['aeat.sii.map.lines']
        sii_map = sii_map_obj.search(
            ['|',
             ('date_from', '<=', self.date),
             ('date_from', '=', False),
             '|',
             ('date_to', '>=', self.date),
             ('date_to', '=', False)], limit=1)
        mapping_taxes = {}
        for code in codes:
            tax_templates = sii_map_line_obj.search(
                [('code', '=', code), ('sii_map_id', '=', sii_map.id)],
                limit=1).taxes
            for tax_template in tax_templates:
                taxes += self.map_sii_tax_template(tax_template, mapping_taxes)
        return taxes

    @api.multi
    def _change_date_format(self, date):
        datetimeobject = fields.Date.from_string(date)
        new_date = datetimeobject.strftime('%d-%m-%Y')
        return new_date

    @api.multi
    def _get_sii_header(self, tipo_comunicacion):
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
    def _get_sii_out_taxes(self):
        """Get the taxes for sales invoices.

        :param self: Single invoice record.
        """
        self.ensure_one()
        taxes_dict = {}
        taxes_f = {}
        taxes_to = {}
        taxes_sfesb = self._get_sii_taxes_map(['SFESB'])
        taxes_sfesbe = self._get_sii_taxes_map(['SFESBE'])
        taxes_sfesisp = self._get_sii_taxes_map(['SFESISP'])
        # taxes_sfesisps = self._get_taxes_map(['SFESISPS'])
        taxes_sfens = self._get_sii_taxes_map(['SFENS'])
        taxes_sfess = self._get_sii_taxes_map(['SFESS'])
        taxes_sfesse = self._get_sii_taxes_map(['SFESSE'])
        for inv_line in self.invoice_line_ids:
            exempt_cause = self._get_sii_exempt_cause(inv_line.product_id)
            for tax_line in inv_line.invoice_line_tax_ids:
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
                    inv_line._update_sii_tax_line(taxes_f, tax_line)
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
                        inv_line._update_sii_tax_line(taxes_to, tax_line)
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
                 and self._get_sii_gen_type() in (2, 3)):
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
        for inv_line in self.invoice_line_ids:
            for tax_line in inv_line.invoice_line_tax_ids:
                if tax_line in taxes_sfrisp:
                    inv_line._update_sii_tax_line(taxes_isp, tax_line)
                elif tax_line in taxes_sfrs:
                    inv_line._update_sii_tax_line(taxes_f, tax_line)
        if taxes_isp:
            taxes_dict.setdefault(
                'InversionSujetoPasivo', {'DetalleIVA': taxes_isp.values()},
            )
        if taxes_f:
            taxes_dict.setdefault(
                'DesgloseIVA', {'DetalleIVA': [taxes_f.values()]},
            )
        return taxes_dict

    @api.multi
    def _get_sii_invoice_dict(self):
        self.ensure_one()
        if not self.partner_id.vat:
            raise exceptions.Warning(
                _("The partner has not a VAT configured.")
            )
        invoice_date = self._change_date_format(self.date)
        company = self.company_id
        ejercicio = fields.Date.from_string(self.date).year
        periodo = '%02d' % fields.Date.from_string(self.date).month
        if not company.chart_template_id:
            raise exceptions.Warning(_(
                'You have to select what account chart template use this'
                ' company.'))
        inv_dict = {}
        if self.type in ['out_invoice', 'out_refund']:
            inv_dict = {
                "IDFactura": {
                    "IDEmisorFactura": {
                        "NIF": company.vat[2:],
                    },
                    "NumSerieFacturaEmisor": self.number[0:60],
                    "FechaExpedicionFacturaEmisor": invoice_date,
                },
                "PeriodoImpositivo": {
                    "Ejercicio": ejercicio,
                    "Periodo": periodo,
                },
                "FacturaExpedida": {
                    # TODO: Incluir los 5 tipos de facturas rectificativas
                    "TipoFactura": (
                        'R4' if self.type == 'out_refund' else 'F1'
                    ),
                    "ClaveRegimenEspecialOTrascendencia": (
                        self.registration_key.code
                    ),
                    "DescripcionOperacion": self.sii_description[0:500],
                    "Contraparte": {
                        "NombreRazon": self.partner_id.name[0:120],
                    },
                    "TipoDesglose": self._get_sii_out_taxes(),
                    "ImporteTotal": self.amount_total,
                }
            }
            exp_dict = inv_dict['FacturaExpedida']
            # Uso condicional de IDOtro/NIF
            exp_dict['Contraparte'].update(self._get_sii_identifier())
            if self.type == 'out_refund':
                exp_dict['TipoRectificativa'] = self.refund_type
                if self.refund_type == 'S':
                    exp_dict['ImporteRectificacion'] = {
                        'BaseRectificada': sum(
                            self.mapped('origin_invoice_ids.amount_untaxed')
                        ),
                        'CuotaRectificada': sum(
                            self.mapped('origin_invoice_ids.amount_tax')
                        ),
                    }
        if self.type in ['in_invoice', 'in_refund']:
            inv_dict = {
                "IDFactura": {
                    "IDEmisorFactura": {},
                    "NumSerieFacturaEmisor": self.reference or ''[:60],
                    "FechaExpedicionFacturaEmisor": invoice_date},
                "PeriodoImpositivo": {
                    "Ejercicio": ejercicio,
                    "Periodo": periodo
                },
                "FacturaRecibida": {
                    # TODO: Incluir los 5 tipos de facturas rectificativas
                    "TipoFactura": (
                        'R4' if self.type == 'in_refund' else 'F1'
                    ),
                    "ClaveRegimenEspecialOTrascendencia": (
                        self.registration_key.code
                    ),
                    "DescripcionOperacion": self.sii_description[0:500],
                    "DesgloseFactura": self._get_sii_in_taxes(),
                    "Contraparte": {
                        "NombreRazon": self.partner_id.name[0:120],
                    },
                    "FechaRegContable": invoice_date,
                    "ImporteTotal": self.amount_total,
                    "CuotaDeducible": self.amount_tax,
                }
            }
            # Uso condicional de IDOtro/NIF
            ident = self._get_sii_identifier()
            inv_dict['IDFactura']['IDEmisorFactura'].update(ident)
            inv_dict['FacturaRecibida']['Contraparte'].update(ident)
            if self.type == 'in_refund':
                rec_dict = inv_dict['FacturaRecibida']
                rec_dict['TipoRectificativa'] = self.refund_type
                if self.refund_type == 'S':
                    rec_dict['ImporteRectificacion'] = {
                        'BaseRectificada': sum(
                            self.mapped('origin_invoice_ids.amount_untaxed')
                        ),
                        'CuotaRectificada': sum(
                            self.mapped('origin_invoice_ids.amount_tax')
                        ),
                    }
        return inv_dict

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
            if not invoice.sii_sent:
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
                # elif invoice.fiscal_position_id.id == self.env.ref(
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
                new_cr = RegistryManager.get(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                invoice = env['account.invoice'].browse(self.id)
                invoice.sii_send_error = fault
                invoice.sii_return = fault
                invoice.sii_send_error = fault
                new_cr.commit()
                new_cr.close()
                raise

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
                    new_delay = self.with_delay().confirm_one_invoice()
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
                    new_delay = self.with_delay().confirm_one_invoice()
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

    @api.multi
    def _get_sii_gen_type(self):
        """Make a choice for general invoice type

        Returns:
            int: 1 (National), 2 (Intracom), 3 (Export)
        """
        self.ensure_one()
        if self.fiscal_position_id.name == u'Régimen Intracomunitario':
            return 2
        elif self.fiscal_position_id.name == \
                u'Régimen Extracomunitario / Canarias, Ceuta y Melilla':
            return 3
        else:
            return 1

    @api.multi
    def _get_sii_identifier(self):
        """Get the SII structure for a partner identifier depending on the
        conditions of the invoice.
        """
        self.ensure_one()
        gen_type = self._get_sii_gen_type()
        # Limpiar alfanum
        vat = ''.join(e for e in self.partner_id.vat if e.isalnum()).upper()
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

    def is_sii_invoice(self):
        """Hook method to be overridden in additional modules to verify
        if the invoice must be sended trough SII system, for special cases.

        :param self: Single invoice record
        :return: bool value indicating if the invoice should be sent to SII.
        """
        self.ensure_one()
        return True

    @job
    @api.multi
    def confirm_one_invoice(self):
        self._send_invoice_to_sii()

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    def _get_sii_line_price_subtotal(self):
        """Obtain the effective invoice line price after discount."""
        self.ensure_one()
        return self.price_unit * (1 - (self.discount or 0.0) / 100.0)

    @api.multi
    def _get_sii_tax_line_req(self):
        """Get any possible tax amounts for 'Recargo equivalencia'."""
        self.ensure_one()
        taxes_re = self.invoice_id._get_sii_taxes_map(['RE'])
        for tax in self.invoice_line_tax_ids:
            if tax in taxes_re:
                price = self._get_sii_line_price_subtotal()
                taxes = tax.compute_all(
                    price, self.quantity, self.invoice_id.currency_id,
                    self.product_id, self.invoice_id.partner_id,
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
        tax_type = tax_line.amount
        if tax_type not in tax_dict:
            tax_dict[tax_type] = {
                'TipoImpositivo': tax_type,
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
            self._get_sii_line_price_subtotal(), self.invoice_id.currency_id,
            self.quantity, self.product_id, self.invoice_id.partner_id,
        )
        tax_dict[tax_type]['BaseImponible'] += taxes['total_excluded']
        if self.invoice_id.type in ['out_invoice', 'out_refund']:
            key = 'CuotaRepercutida'
        else:
            key = 'CuotaSoportada'
        tax_dict[tax_type][key] += taxes['taxes'][0]['amount']

