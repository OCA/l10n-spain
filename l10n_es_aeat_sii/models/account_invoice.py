# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Studio73 - Pablo Fuentes <pablo@studio73>
# Copyright 2017 Studio73 - Jordi Tolsà <jordi@studio73.es>
# Copyright 2018 Javi Melendez <javimelex@gmail.com>
# Copyright 2018 PESOL - Angel Moya <angel.moya@pesol.es>
# Copyright 2011-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import json

from odoo import _, api, fields, exceptions, models
from odoo.tools.float_utils import float_compare
from requests import Session

from odoo.modules.registry import Registry

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

SII_STATES = [
    ('not_sent', 'Not sent'),
    ('sent', 'Sent'),
    ('sent_w_errors', 'Accepted with errors'),
    ('sent_modified', 'Registered in SII but last modifications not sent'),
    ('cancelled', 'Cancelled'),
    ('cancelled_modified', 'Cancelled in SII but last modifications not sent'),
]
SII_VERSION = '1.1'
SII_COUNTRY_CODE_MAPPING = {
    'RE': 'FR',
    'GP': 'FR',
    'MQ': 'FR',
    'GF': 'FR',
}
SII_MACRODATA_LIMIT = 100000000.0
SII_VALID_INVOICE_STATES = ['open', 'in_payment', 'paid']


def round_by_keys(elem, search_keys, prec=2):
    """ This uses ``round`` method directly as if has been tested that Odoo's
        ``float_round`` still returns incorrect amounts for certain values. Try
        3 units x 3,77 €/unit with 10% tax and you will be hit by the error
        (on regular x86 architectures)."""
    if isinstance(elem, dict):
        for key, value in elem.items():
            if key in search_keys:
                elem[key] = round(elem[key], prec)
            else:
                round_by_keys(value, search_keys)
    elif isinstance(elem, list):
        for value in elem:
            round_by_keys(value, search_keys)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    SII_WDSL_MAPPING = {
        'out_invoice': 'l10n_es_aeat_sii.wsdl_out',
        'out_refund': 'l10n_es_aeat_sii.wsdl_out',
        'in_invoice': 'l10n_es_aeat_sii.wsdl_in',
        'in_refund': 'l10n_es_aeat_sii.wsdl_in',
    }
    SII_PORT_NAME_MAPPING = {
        'out_invoice': 'SuministroFactEmitidas',
        'out_refund': 'SuministroFactEmitidas',
        'in_invoice': 'SuministroFactRecibidas',
        'in_refund': 'SuministroFactRecibidas',
    }

    def _get_default_type(self):
        context = self.env.context
        return context.get('type', context.get("default_type"))

    def _default_sii_refund_type(self):
        inv_type = self._get_default_type()
        return 'I' if inv_type in ['out_refund', 'in_refund'] else False

    def _default_sii_registration_key(self):
        sii_key_obj = self.env['aeat.sii.mapping.registration.keys']
        invoice_type = self._get_default_type()
        if invoice_type in ['in_invoice', 'in_refund']:
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
        readonly=True, copy=False,
        help="Indicates the state of this invoice in relation with the "
             "presentation at the SII",
    )
    sii_csv = fields.Char(string='SII CSV', copy=False, readonly=True)
    sii_return = fields.Text(string='SII Return', copy=False, readonly=True)
    sii_header_sent = fields.Text(
        string="SII last header sent", copy=False, readonly=True,
    )
    sii_content_sent = fields.Text(
        string="SII last content sent", copy=False, readonly=True,
    )
    sii_send_error = fields.Text(
        string='SII Send Error', readonly=True, copy=False,
    )
    sii_send_failed = fields.Boolean(
        string="SII send failed", copy=False,
        help="Indicates that the last attempt to communicate this invoice to "
             "the SII has failed. See SII return for details",
    )
    sii_refund_type = fields.Selection(
        selection=[
            # ('S', 'By substitution'), - Removed as not fully supported
            ('I', 'By differences'),
        ],
        string="SII Refund Type",
        default=lambda self: self._default_sii_refund_type(),
        oldname='refund_type',
    )
    sii_refund_specific_invoice_type = fields.Selection(
        selection=[
            ('R1', 'Error based on law and Art. 80 One and Two LIVA (R1)'),
            ('R2', 'Art. 80 Three LIVA - Bankruptcy (R2)'),
            ('R3', 'Art. 80 Four LIVA - Bad debt (R3)'),
            ('R4', 'Rest of causes (R4)'),
        ],
        help="Fill this field when the refund are one of the specific cases"
             " of article 80 of LIVA for notifying to SII with the proper"
             " invoice type.",
    )
    sii_account_registration_date = fields.Date(
        string='SII account registration date', readonly=True, copy=False,
        help="Indicates the account registration date set at the SII, which "
             "must be the date when the invoice is recorded in the system and "
             "is independent of the date of the accounting entry of the "
             "invoice")
    sii_registration_key = fields.Many2one(
        comodel_name='aeat.sii.mapping.registration.keys',
        string="SII registration key", default=_default_sii_registration_key,
        oldname='registration_key',
        # required=True, This is not set as required here to avoid the
        # set not null constraint warning
    )
    sii_registration_key_additional1 = fields.Many2one(
        comodel_name='aeat.sii.mapping.registration.keys',
        string="Additional SII registration key"
    )
    sii_registration_key_additional2 = fields.Many2one(
        comodel_name='aeat.sii.mapping.registration.keys',
        string="Additional 2 SII registration key"
    )
    sii_registration_key_code = fields.Char(
        related="sii_registration_key.code", readonly=True,
    )
    sii_enabled = fields.Boolean(
        string='Enable SII', compute='_compute_sii_enabled',
    )
    sii_property_location = fields.Selection(
        string="Real property location", copy=False,
        selection=[
            ('1', '[1]-Real property with cadastral code located within '
                  'the Spanish territory except Basque Country or Navarra'),
            ('2', '[2]-Real property located in the '
                  'Basque Country or Navarra'),
            ('3', '[3]-Real property in any of the above situations '
                  'but without cadastral code'),
            ('4', '[4]-Real property located in a foreign country'),
        ],
    )
    sii_property_cadastrial_code = fields.Char(
        string="Real property cadastrial code", size=25, copy=False,
    )
    sii_macrodata = fields.Boolean(
        string="MacroData",
        help="Check to confirm that the invoice has an absolute amount "
             "greater o equal to 100 000 000,00 euros.",
        compute='_compute_macrodata',
    )
    invoice_jobs_ids = fields.Many2many(
        comodel_name='queue.job', column1='invoice_id', column2='job_id',
        string="Connector Jobs", copy=False,
    )

    @api.depends('amount_total')
    def _compute_macrodata(self):
        for inv in self:
            inv.sii_macrodata = True if float_compare(
                inv.amount_total,
                SII_MACRODATA_LIMIT,
                precision_digits=2
            ) >= 0 else False

    @api.onchange('sii_refund_type')
    def onchange_sii_refund_type(self):
        if (self.sii_enabled and self.sii_refund_type == 'S' and
                not self.refund_invoice_id):
            self.sii_refund_type = False
            return {
                'warning': {
                    'message': _(
                        'You must have at least one refunded invoice'
                    ),
                }
            }

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        """Trigger fiscal position onchange for assigning SII key when creating
        bills from purchase module with the button from PO, due to the special
        way this is triggered through chained onchanges.
        """
        trigger_fp = (
            self.partner_id.property_account_position_id !=
            self.fiscal_position_id
        )
        res = super()._onchange_partner_id()
        if trigger_fp:
            self.onchange_fiscal_position_id_l10n_es_aeat_sii()
        return res

    @api.onchange('fiscal_position_id')
    def onchange_fiscal_position_id_l10n_es_aeat_sii(self):
        for invoice in self.filtered('fiscal_position_id'):
            if 'out' in invoice.type:
                key = invoice.fiscal_position_id.sii_registration_key_sale
            else:
                key = invoice.fiscal_position_id.sii_registration_key_purchase
            invoice.sii_registration_key = key

    @api.model
    def create(self, vals):
        """Complete registration key for auto-generated invoices."""
        if ('refund' in vals.get('type', '') and
                not vals.get('sii_refund_type')):
            vals['sii_refund_type'] = 'I'
        invoice = super(AccountInvoice, self).create(vals)
        if (vals.get('fiscal_position_id') and
                not vals.get('sii_registration_key')):
            invoice.onchange_fiscal_position_id_l10n_es_aeat_sii()
        return invoice

    @api.multi
    def write(self, vals):
        """For supplier invoices the SII primary key is the supplier
        VAT/ID Otro and the supplier invoice number. Cannot let change these
        values in a SII registered supplier invoice"""
        for invoice in self.filtered(lambda x: x.sii_state != 'not_sent'):
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
                elif 'reference' in vals:
                    raise exceptions.Warning(
                        _("You cannot change the supplier invoice number of "
                          "an invoice already registered at the SII. You must "
                          "cancel the invoice and create a new one with the "
                          "correct number")
                    )
        # Fill sii_refund_type if not set previously. It happens on sales
        # order invoicing process for example.
        if (vals.get('type') and not vals.get('sii_refund_type') and
                not any(self.mapped('sii_refund_type'))):
            vals['sii_refund_type'] = 'I'
        res = super(AccountInvoice, self).write(vals)
        if (vals.get('fiscal_position_id') and
                not vals.get('sii_registration_key')):
            self.onchange_fiscal_position_id_l10n_es_aeat_sii()
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
    def _get_sii_taxes_map(self, codes):
        """Return the codes that correspond to that sii map line codes.

        :param self: Single invoice record.
        :param codes: List of code strings to get the mapping.
        :return: Recordset with the corresponding codes
        """
        self.ensure_one()
        sii_map = self.env['aeat.sii.map'].search(
            ['|',
             ('date_from', '<=', self.date),
             ('date_from', '=', False),
             '|',
             ('date_to', '>=', self.date),
             ('date_to', '=', False)], limit=1)
        tax_templates = sii_map.sudo().map_lines.filtered(
            lambda x: x.code in codes
        ).taxes
        return self.company_id.get_taxes_from_templates(tax_templates)

    @api.multi
    def _change_date_format(self, date):
        datetimeobject = fields.Date.to_date(date)
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
    def _get_sii_tax_line_req(self, tax):
        """Get the invoice tax line for 'Recargo equivalencia'.

        :param self: Single invoice record.
        :param tax: Initial tax for searching for the RE twin tax.
        :return: Invoice tax line (if any) for the correspondent RE tax.
        """
        self.ensure_one()
        taxes_re = self._get_sii_taxes_map(['RE'])
        inv_lines = self.invoice_line_ids.filtered(
            lambda x: tax in x.mapped('invoice_line_tax_ids')
        )
        re_tax = inv_lines.mapped('invoice_line_tax_ids').filtered(
            lambda x: x in taxes_re
        )
        if len(re_tax) > 1:
            raise exceptions.UserError(
                _("There's a mismatch in taxes for RE. Check them.")
            )
        return self.tax_line_ids.filtered(lambda x: x.tax_id == re_tax)

    @api.model
    def _get_sii_tax_dict(self, tax_line, sign):
        """Get the SII tax dictionary for the passed tax line.

        :param self: Single invoice record.
        :param tax_line: Tax line that is being analyzed.
        :param sign: Sign of the operation (only refund by differences is
          negative).
        :return: A dictionary with the corresponding SII tax values.
        """
        tax = tax_line.tax_id
        if tax.amount_type == 'group':
            tax_type = abs(tax.children_tax_ids.filtered('amount')[:1].amount)
        else:
            tax_type = abs(tax.amount)
        tax_dict = {
            'TipoImpositivo': str(tax_type),
            'BaseImponible': sign * tax_line.base_company,
        }
        if self.type in ['out_invoice', 'out_refund']:
            key = 'CuotaRepercutida'
        else:
            key = 'CuotaSoportada'
        tax_dict[key] = sign * tax_line.amount_company
        # Recargo de equivalencia
        re_tax_line = self._get_sii_tax_line_req(tax)
        if re_tax_line:
            tax_dict['TipoRecargoEquivalencia'] = (
                abs(re_tax_line.tax_id.amount)
            )
            tax_dict['CuotaRecargoEquivalencia'] = (
                sign * re_tax_line.amount_company
            )
        return tax_dict

    def _is_sii_type_breakdown_required(self, taxes_dict):
        """Calculates if the block 'DesgloseTipoOperacion' is required for
        the invoice communication."""
        self.ensure_one()
        if 'DesgloseFactura' not in taxes_dict:
            return False
        country_code = self._get_sii_country_code()
        sii_gen_type = self._get_sii_gen_type()
        if 'DesgloseTipoOperacion' in taxes_dict:
            # DesgloseTipoOperacion and DesgloseFactura are Exclusive
            return True
        elif sii_gen_type in (2, 3):
            # DesgloseTipoOperacion required for Intracommunity and
            # Export operations
            return True
        elif sii_gen_type == 1 and country_code != 'ES':
            # DesgloseTipoOperacion required for national operations
            # with 'IDOtro' in the SII identifier block
            return True
        elif (sii_gen_type == 1 and
                (self.partner_id.vat or '').startswith('ESN')):
            # DesgloseTipoOperacion required if customer's country is Spain and
            # has a NIF which starts with 'N'
            return True
        return False

    @api.multi
    def _get_sii_out_taxes(self):
        """Get the taxes for sales invoices.

        :param self: Single invoice record.
        """
        self.ensure_one()
        taxes_dict = {}
        taxes_sfesb = self._get_sii_taxes_map(['SFESB'])
        taxes_sfesbe = self._get_sii_taxes_map(['SFESBE'])
        taxes_sfesisp = self._get_sii_taxes_map(['SFESISP'])
        # taxes_sfesisps = self._get_taxes_map(['SFESISPS'])
        taxes_sfens = self._get_sii_taxes_map(['SFENS'])
        taxes_sfess = self._get_sii_taxes_map(['SFESS'])
        taxes_sfesse = self._get_sii_taxes_map(['SFESSE'])
        taxes_sfesns = self._get_sii_taxes_map(['SFESNS'])
        taxes_not_in_total = self._get_sii_taxes_map(['NotIncludedInTotal'])
        base_not_in_total = self._get_sii_taxes_map(['BaseNotIncludedInTotal'])
        # Check if refund type is 'By differences'. Negative amounts!
        sign = self._get_sii_sign()
        not_in_amount_total = 0
        exempt_cause = self._get_sii_exempt_cause(taxes_sfesbe + taxes_sfesse)
        for tax_line in self.tax_line_ids:
            tax = tax_line.tax_id
            breakdown_taxes = (
                taxes_sfesb + taxes_sfesisp + taxes_sfens + taxes_sfesbe
            )
            if tax in (taxes_not_in_total + base_not_in_total):
                amount = (
                    tax_line.base if tax in base_not_in_total else tax_line.amount_total
                )
                if self.currency_id != self.company_id.currency_id:
                    amount = self.currency_id._convert(
                        amount,
                        self.company_id.currency_id,
                        self.company_id,
                        self._get_currency_rate_date(),
                    )
                not_in_amount_total += amount
            if tax in breakdown_taxes:
                tax_breakdown = taxes_dict.setdefault(
                    'DesgloseFactura', {},
                )
            if tax in (taxes_sfesb + taxes_sfesbe + taxes_sfesisp):
                sub_dict = tax_breakdown.setdefault('Sujeta', {})
                # TODO l10n_es no tiene impuesto exento de bienes
                # corrientes nacionales
                if tax in taxes_sfesbe:
                    exempt_dict = sub_dict.setdefault(
                        'Exenta', {'DetalleExenta': [{'BaseImponible': 0}]},
                    )
                    det_dict = exempt_dict['DetalleExenta'][0]
                    if exempt_cause:
                        det_dict['CausaExencion'] = exempt_cause
                    det_dict['BaseImponible'] += (
                        tax_line.base_company * sign)
                else:
                    sub_dict.setdefault('NoExenta', {
                        'TipoNoExenta': (
                            'S2' if tax in taxes_sfesisp else 'S1'
                        ),
                        'DesgloseIVA': {
                            'DetalleIVA': [],
                        },
                    })
                    not_ex_type = sub_dict['NoExenta']['TipoNoExenta']
                    if tax in taxes_sfesisp:
                        is_s3 = not_ex_type == 'S1'
                    else:
                        is_s3 = not_ex_type == 'S2'
                    if is_s3:
                        sub_dict['NoExenta']['TipoNoExenta'] = 'S3'
                    sub_dict['NoExenta']['DesgloseIVA']['DetalleIVA'].append(
                        self._get_sii_tax_dict(tax_line, sign),
                    )
            # No sujetas
            if tax in taxes_sfens:
                # ImporteTAIReglasLocalizacion or ImportePorArticulos7_14_Otros
                default_no_taxable_cause = self._get_no_taxable_cause()
                nsub_dict = tax_breakdown.setdefault(
                    'NoSujeta', {default_no_taxable_cause: 0},
                )
                nsub_dict[default_no_taxable_cause] += (
                    tax_line.base_company * sign)
            if tax in (taxes_sfess + taxes_sfesse + taxes_sfesns):
                type_breakdown = taxes_dict.setdefault(
                    'DesgloseTipoOperacion', {
                        'PrestacionServicios': {},
                    },
                )
                if tax in (taxes_sfesse + taxes_sfess):
                    type_breakdown['PrestacionServicios'].setdefault(
                        'Sujeta', {}
                    )
                service_dict = type_breakdown['PrestacionServicios']
                if tax in taxes_sfesse:
                    exempt_dict = service_dict['Sujeta'].setdefault(
                        'Exenta', {'DetalleExenta': [{'BaseImponible': 0}]},
                    )
                    det_dict = exempt_dict['DetalleExenta'][0]
                    if exempt_cause:
                        det_dict['CausaExencion'] = exempt_cause
                    det_dict['BaseImponible'] += (
                        tax_line.base_company * sign)
                if tax in taxes_sfess:
                    # TODO l10n_es_ no tiene impuesto ISP de servicios
                    # if tax in taxes_sfesisps:
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
                    sub = type_breakdown['PrestacionServicios']['Sujeta'][
                        'NoExenta']['DesgloseIVA']['DetalleIVA']
                    sub.append(self._get_sii_tax_dict(tax_line, sign))
                if tax in taxes_sfesns:
                    nsub_dict = service_dict.setdefault(
                        'NoSujeta', {'ImporteTAIReglasLocalizacion': 0},
                    )
                    nsub_dict['ImporteTAIReglasLocalizacion'] += (
                        tax_line.base_company * sign
                    )
        # Ajustes finales breakdown
        # - DesgloseFactura y DesgloseTipoOperacion son excluyentes
        # - Ciertos condicionantes obligan DesgloseTipoOperacion
        if self._is_sii_type_breakdown_required(taxes_dict):
            taxes_dict.setdefault('DesgloseTipoOperacion', {})
            taxes_dict['DesgloseTipoOperacion']['Entrega'] = \
                taxes_dict['DesgloseFactura']
            del taxes_dict['DesgloseFactura']
        return taxes_dict, not_in_amount_total

    @api.model
    def _merge_tax_dict(self, vat_list, tax_dict, comp_key, merge_keys):
        """Helper method for merging values in an existing tax dictionary."""
        for existing_dict in vat_list:
            if (existing_dict.get(comp_key, "-99") ==
                    tax_dict.get(comp_key, "-99")):
                for key in merge_keys:
                    existing_dict[key] += tax_dict[key]
                return True
        return False

    @api.multi
    def _get_sii_in_taxes(self):
        """Get the taxes for purchase invoices.

        :param self:  Single invoice record.
        """
        self.ensure_one()
        taxes_dict = {}
        taxes_sfrs = self._get_sii_taxes_map(['SFRS'])
        taxes_sfrsa = self._get_sii_taxes_map(['SFRSA'])
        taxes_sfrisp = self._get_sii_taxes_map(['SFRISP'])
        taxes_sfrns = self._get_sii_taxes_map(['SFRNS'])
        taxes_sfrnd = self._get_sii_taxes_map(['SFRND'])
        taxes_not_in_total = self._get_sii_taxes_map(['NotIncludedInTotal'])
        base_not_in_total = self._get_sii_taxes_map(['BaseNotIncludedInTotal'])
        tax_amount = 0.0
        not_in_amount_total = 0.0
        # Check if refund type is 'By differences'. Negative amounts!
        sign = self._get_sii_sign()
        for tax_line in self.tax_line_ids:
            tax = tax_line.tax_id
            if tax in (taxes_not_in_total + base_not_in_total):
                amount = (
                    tax_line.base if tax in base_not_in_total else tax_line.amount_total
                )
                if self.currency_id != self.company_id.currency_id:
                    amount = self.currency_id._convert(
                        amount,
                        self.company_id.currency_id,
                        self.company_id,
                        self._get_currency_rate_date(),
                    )
                not_in_amount_total += amount
            if tax in taxes_sfrisp:
                base_dict = taxes_dict.setdefault(
                    'InversionSujetoPasivo', {'DetalleIVA': []},
                )
            elif tax in taxes_sfrs + taxes_sfrns + taxes_sfrsa + taxes_sfrnd:
                base_dict = taxes_dict.setdefault(
                    'DesgloseIVA', {'DetalleIVA': []},
                )
            else:
                continue
            tax_dict = self._get_sii_tax_dict(tax_line, sign)
            if tax in taxes_sfrisp + taxes_sfrs:
                tax_amount += tax_line.amount_company
            if tax in taxes_sfrns:
                tax_dict.pop("TipoImpositivo")
                tax_dict.pop("CuotaSoportada")
                base_dict['DetalleIVA'].append(tax_dict)
            elif tax in taxes_sfrsa:
                tax_dict['PorcentCompensacionREAGYP'] = tax_dict.pop(
                    'TipoImpositivo'
                )
                tax_dict['ImporteCompensacionREAGYP'] = tax_dict.pop(
                    'CuotaSoportada'
                )
                base_dict['DetalleIVA'].append(tax_dict)
            else:
                if not self._merge_tax_dict(
                    base_dict['DetalleIVA'], tax_dict, "TipoImpositivo",
                    ["BaseImponible", "CuotaSoportada"]
                ):
                    base_dict['DetalleIVA'].append(tax_dict)
        return taxes_dict, tax_amount, not_in_amount_total

    @api.multi
    def _is_sii_simplified_invoice(self):
        """Inheritable method to allow control when an
        invoice are simplified or normal"""
        partner = self.partner_id.commercial_partner_id
        is_simplified = partner.sii_simplified_invoice
        return is_simplified

    @api.multi
    def _sii_check_exceptions(self):
        """Inheritable method for exceptions control when sending SII invoices.
        """
        self.ensure_one()
        gen_type = self._get_sii_gen_type()
        partner = self.partner_id.commercial_partner_id
        country_code = self._get_sii_country_code()
        is_simplified_invoice = self._is_sii_simplified_invoice()

        if is_simplified_invoice and self.type[:2] == 'in':
            raise exceptions.Warning(
                _("You can't make a supplier simplified invoice.")
            )
        if ((gen_type != 3 or country_code == 'ES') and
                not partner.vat and not is_simplified_invoice):
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
        if not self.reference and self.type in ['in_invoice', 'in_refund']:
            raise exceptions.Warning(
                _("The supplier number invoice is required")
            )

    @api.multi
    def _get_account_registration_date(self):
        """Hook method to allow the setting of the account registration date
        of each supplier invoice. The SII recommends to set the send date as
        the default value (point 9.3 of the document
        SII_Descripcion_ServicioWeb_v0.7.pdf), so by default we return
        the current date or, if exists, the stored
        sii_account_registration_date
        :return String date in the format %Y-%m-%d"""
        self.ensure_one()
        return self.sii_account_registration_date or fields.Date.today()

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
        ejercicio = fields.Date.to_date(self.date).year
        periodo = '%02d' % fields.Date.to_date(self.date).month
        is_simplified_invoice = self._is_sii_simplified_invoice()
        inv_dict = {
            "IDFactura": {
                "IDEmisorFactura": {
                    "NIF": company.vat[2:],
                },
                # On cancelled invoices, number is not filled
                "NumSerieFacturaEmisor": (
                    self.number or self.move_name or ''
                )[0:60],
                "FechaExpedicionFacturaEmisor": invoice_date,
            },
            "PeriodoLiquidacion": {
                "Ejercicio": ejercicio,
                "Periodo": periodo,
            },
        }
        if not cancel:
            # Check if refund type is 'By differences'. Negative amounts!
            sign = self._get_sii_sign()
            tipo_desglose, not_in_amount_total = self._get_sii_out_taxes()
            amount_total = (
                abs(self.amount_total_company_signed) - not_in_amount_total
            ) * sign
            if self.type == 'out_refund':
                if self.sii_refund_specific_invoice_type:
                    tipo_factura = self.sii_refund_specific_invoice_type
                else:
                    tipo_factura = 'R5' if is_simplified_invoice else 'R1'
            else:
                tipo_factura = 'F2' if is_simplified_invoice else 'F1'
            inv_dict["FacturaExpedida"] = {
                "TipoFactura": tipo_factura,
                "ClaveRegimenEspecialOTrascendencia": (
                    self.sii_registration_key.code
                ),
                "DescripcionOperacion": self.sii_description,
                "TipoDesglose": tipo_desglose,
                "ImporteTotal": amount_total,
            }
            if self.sii_macrodata:
                inv_dict["FacturaExpedida"].update(Macrodato="S")
            if self.sii_registration_key_additional1:
                inv_dict["FacturaExpedida"].\
                    update({'ClaveRegimenEspecialOTrascendenciaAdicional1': (
                        self.sii_registration_key_additional1.code)})
            if self.sii_registration_key_additional2:
                inv_dict["FacturaExpedida"].\
                    update({'ClaveRegimenEspecialOTrascendenciaAdicional2': (
                        self.sii_registration_key_additional2.code)})
            if self.sii_registration_key.code in ['12', '13']:
                inv_dict["FacturaExpedida"]['DatosInmueble'] = {
                    'DetalleInmueble': {
                        'SituacionInmueble': self.sii_property_location,
                        'ReferenciaCatastral': (
                            self.sii_property_cadastrial_code or '')
                    }
                }
            exp_dict = inv_dict['FacturaExpedida']
            if not is_simplified_invoice:
                # Simplified invoices don't have counterpart
                exp_dict["Contraparte"] = {
                    "NombreRazon": partner.name[0:120],
                }
                # Uso condicional de IDOtro/NIF
                exp_dict['Contraparte'].update(self._get_sii_identifier())
            if self.type == 'out_refund':
                exp_dict['TipoRectificativa'] = self.sii_refund_type
                if self.sii_refund_type == 'S':
                    origin = self.refund_invoice_id
                    exp_dict['ImporteRectificacion'] = {
                        'BaseRectificada': abs(
                            origin.amount_untaxed_signed
                        ),
                        'CuotaRectificada': abs(
                            origin.amount_total_company_signed -
                            origin.amount_untaxed_signed
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
            self._get_account_registration_date())
        ejercicio = fields.Date.to_date(self.date).year
        periodo = '%02d' % fields.Date.to_date(self.date).month
        desglose_factura, tax_amount, not_in_amount_total = (
            self._get_sii_in_taxes())
        inv_dict = {
            "IDFactura": {
                "IDEmisorFactura": {},
                "NumSerieFacturaEmisor": (
                    (self.reference or '')[:60]
                ),
                "FechaExpedicionFacturaEmisor": invoice_date},
            "PeriodoLiquidacion": {
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
            amount_total = (
                abs(self.amount_total_company_signed) - not_in_amount_total
            ) * sign
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
                "ImporteTotal": amount_total,
                "CuotaDeducible": tax_amount * sign,
            }
            if self.sii_macrodata:
                inv_dict["FacturaRecibida"].update(Macrodato="S")
            if self.sii_registration_key_additional1:
                inv_dict["FacturaRecibida"].\
                    update({'ClaveRegimenEspecialOTrascendenciaAdicional1': (
                        self.sii_registration_key_additional1.code)})
            if self.sii_registration_key_additional2:
                inv_dict["FacturaRecibida"].\
                    update({'ClaveRegimenEspecialOTrascendenciaAdicional2': (
                        self.sii_registration_key_additional2.code)})
            # Uso condicional de IDOtro/NIF
            inv_dict['FacturaRecibida']['Contraparte'].update(ident)
            if self.type == 'in_refund':
                rec_dict = inv_dict['FacturaRecibida']
                rec_dict['TipoRectificativa'] = self.sii_refund_type
                if self.sii_refund_type == 'S':
                    refund_tax_amount = (
                        self.refund_invoice_id._get_sii_in_taxes()[1]
                    )
                    rec_dict['ImporteRectificacion'] = {
                        'BaseRectificada': abs(
                            self.refund_invoice_id.amount_untaxed_signed
                        ),
                        'CuotaRectificada': refund_tax_amount,
                    }
        return inv_dict

    @api.multi
    def _get_sii_invoice_dict(self):
        self.ensure_one()
        self._sii_check_exceptions()
        inv_dict = {}
        if self.type in ['out_invoice', 'out_refund']:
            inv_dict = self._get_sii_invoice_dict_out()
        elif self.type in ['in_invoice', 'in_refund']:
            inv_dict = self._get_sii_invoice_dict_in()
        round_by_keys(
            inv_dict, [
                'BaseImponible',
                'CuotaRepercutida',
                'CuotaSoportada',
                'TipoRecargoEquivalencia',
                'CuotaRecargoEquivalencia',
                'ImportePorArticulos7_14_Otros',
                'ImporteTAIReglasLocalizacion',
                'ImporteTotal',
                'BaseRectificada',
                'CuotaRectificada',
                'CuotaDeducible',
                'ImporteCompensacionREAGYP',
            ],
        )
        return inv_dict

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
    def _connect_params_sii(self, mapping_key):
        self.ensure_one()
        params = {
            'wsdl': self.env['ir.config_parameter'].sudo().get_param(
                self.SII_WDSL_MAPPING[mapping_key], False
            ),
            'port_name': self.SII_PORT_NAME_MAPPING[mapping_key],
            'address': False,
        }
        agency = self.company_id.sii_tax_agency_id
        if agency:
            params.update(agency._connect_params_sii(
                mapping_key, self.company_id))
        if not params['address'] and self.company_id.sii_test:
            params['port_name'] += 'Pruebas'
        return params

    @api.multi
    def _connect_sii(self, mapping_key):
        self.ensure_one()
        params = self._connect_params_sii(mapping_key)
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
            public_crt = self.env['ir.config_parameter'].sudo().get_param(
                'l10n_es_aeat_sii.publicCrt', False)
            private_key = self.env['ir.config_parameter'].sudo().get_param(
                'l10n_es_aeat_sii.privateKey', False)
        session = Session()
        session.cert = (public_crt, private_key)
        transport = Transport(session=session)
        history = HistoryPlugin()
        client = Client(
            wsdl=params['wsdl'], transport=transport, plugins=[history],
        )
        return self._bind_sii(client, params['port_name'], params['address'])

    @api.multi
    def _bind_sii(self, client, port_name, address=None):
        self.ensure_one()
        service = client._get_service('siiService')
        port = client._get_port(service, port_name)
        address = address or port.binding_options['address']
        return client.create_service(port.binding.name, address)

    @api.multi
    def _process_invoice_for_sii_send(self):
        """Process invoices for sending to the SII. Adds general checks from
        configuration parameters and invoice availability for SII. If the
        invoice is to be sent the decides the send method: direct send or
        via connector depending on 'Use connector' configuration"""
        queue_obj = self.env['queue.job'].sudo()
        for invoice in self:
            company = invoice.company_id
            if not company.use_connector:
                invoice._send_invoice_to_sii()
            else:
                eta = company._get_sii_eta()
                new_delay = invoice.sudo().with_context(
                    company_id=company.id
                ).with_delay(
                    eta=eta if not invoice.sii_send_failed else False,
                ).confirm_one_invoice()
                job = queue_obj.search([
                    ('uuid', '=', new_delay.uuid)
                ], limit=1)
                invoice.sudo().invoice_jobs_ids |= job

    @api.multi
    def _send_invoice_to_sii(self):
        for invoice in self.filtered(
            lambda i: i.state in SII_VALID_INVOICE_STATES
        ):
            serv = invoice._connect_sii(invoice.type)
            if invoice.sii_state == 'not_sent':
                tipo_comunicacion = 'A0'
            else:
                tipo_comunicacion = 'A1'
            header = invoice._get_sii_header(tipo_comunicacion)
            inv_vals = {
                'sii_header_sent': json.dumps(header, indent=4),
            }
            try:
                inv_dict = invoice._get_sii_invoice_dict()
                inv_vals['sii_content_sent'] = json.dumps(inv_dict, indent=4)
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
                res_line = res['RespuestaLinea'][0]
                if res['EstadoEnvio'] == 'Correcto':
                    inv_vals.update({
                        'sii_state': 'sent',
                        'sii_csv': res['CSV'],
                        'sii_send_failed': False,
                    })
                elif res['EstadoEnvio'] == 'ParcialmenteCorrecto' and \
                        res_line['EstadoRegistro'] == 'AceptadoConErrores':
                    inv_vals.update({
                        'sii_state': 'sent_w_errors',
                        'sii_csv': res['CSV'],
                        'sii_send_failed': True,
                    })
                else:
                    inv_vals['sii_send_failed'] = True
                if ('sii_state' in inv_vals and
                        not invoice.sii_account_registration_date and
                        invoice.type[:2] == 'in'):
                    inv_vals['sii_account_registration_date'] = (
                        self._get_account_registration_date()
                    )
                inv_vals['sii_return'] = res
                send_error = False
                if res_line['CodigoErrorRegistro']:
                    send_error = "{} | {}".format(
                        str(res_line['CodigoErrorRegistro']),
                        str(res_line['DescripcionErrorRegistro'])[:60])
                inv_vals['sii_send_error'] = send_error
                invoice.write(inv_vals)
            except Exception as fault:
                new_cr = Registry(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                invoice = env['account.invoice'].browse(invoice.id)
                inv_vals.update({
                    'sii_send_failed': True,
                    'sii_send_error': repr(fault)[:60],
                    'sii_return': repr(fault),
                })
                invoice.write(inv_vals)
                new_cr.commit()
                new_cr.close()
                raise

    @api.multi
    def _sii_invoice_dict_not_modified(self):
        self.ensure_one()
        to_send = self._get_sii_invoice_dict()
        content_sent = json.loads(self.sii_content_sent)
        return to_send == content_sent

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for invoice in self.filtered('sii_enabled'):
            if invoice.sii_state in ['sent_modified', 'sent'] and \
                    self._sii_invoice_dict_not_modified():
                if invoice.sii_state == 'sent_modified':
                    invoice.sii_state = 'sent'
                continue
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
                i.sii_enabled and i.state in SII_VALID_INVOICE_STATES and
                i.sii_state not in ['sent', 'cancelled']
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
            serv = invoice._connect_sii(invoice.type)
            header = invoice._get_sii_header(cancellation=True)
            inv_vals = {
                'sii_send_failed': True,
                'sii_send_error': False,
            }
            try:
                inv_dict = invoice._get_cancel_sii_invoice_dict()
                if invoice.type in ['out_invoice', 'out_refund']:
                    res = serv.AnulacionLRFacturasEmitidas(header, inv_dict)
                else:
                    res = serv.AnulacionLRFacturasRecibidas(header, inv_dict)
                # TODO Facturas intracomunitarias 66 RIVA
                # elif invoice.fiscal_position_id.id == self.env.ref(
                #     'account.fp_intra').id:
                #     res = serv.AnulacionLRDetOperacionIntracomunitaria(
                #         header, invoices)
                inv_vals['sii_return'] = res
                if res['EstadoEnvio'] == 'Correcto':
                    inv_vals.update({
                        'sii_state': 'cancelled',
                        'sii_csv': res['CSV'],
                        'sii_send_failed': False,
                    })
                res_line = res['RespuestaLinea'][0]
                if res_line['CodigoErrorRegistro']:
                    inv_vals['sii_send_error'] = u"{} | {}".format(
                        str(res_line['CodigoErrorRegistro']),
                        str(res_line['DescripcionErrorRegistro'])[:60],
                    )
                invoice.write(inv_vals)
            except Exception as fault:
                new_cr = Registry(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                invoice = env['account.invoice'].browse(invoice.id)
                inv_vals.update({
                    'sii_send_failed': True,
                    'sii_send_error': repr(fault)[:60],
                    'sii_return': repr(fault),
                })
                invoice.write(inv_vals)
                new_cr.commit()
                new_cr.close()
                raise

    @api.multi
    def cancel_sii(self):
        invoices = self.filtered(
            lambda i: (i.sii_enabled and i.state in ['cancel'] and
                       i.sii_state in ['sent', 'sent_w_errors',
                                       'sent_modified'])
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
                new_delay = self.sudo().with_context(
                    company_id=company.id,
                ).with_delay(eta=eta).cancel_one_invoice()
                job = queue_obj.search([
                    ('uuid', '=', new_delay.uuid)
                ], limit=1)
                invoice.sudo().invoice_jobs_ids |= job

    @api.multi
    def _cancel_invoice_jobs(self):
        for queue in self.sudo().mapped('invoice_jobs_ids'):
            if queue.state == 'started':
                return False
            elif queue.state in ('pending', 'enqueued', 'failed'):
                queue.unlink()
        return True

    @api.multi
    def action_cancel(self):
        if not self._cancel_invoice_jobs():
            raise exceptions.Warning(_(
                'You can not cancel this invoice because'
                ' there is a job running!'))
        res = super(AccountInvoice, self).action_cancel()
        for invoice in self:
            if invoice.sii_state == 'sent':
                invoice.sii_state = 'sent_modified'
            elif invoice.sii_state == 'cancelled_modified':
                # Case when repoen a cancelled invoice, validate and cancel
                # again without any SII communication.
                invoice.sii_state = 'cancelled'
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
        partner_ident = self.fiscal_position_id.sii_partner_identification_type
        if partner_ident:
            res = int(partner_ident)
        elif self.fiscal_position_id.name == 'Régimen Intracomunitario':
            res = 2
        elif self.fiscal_position_id.name == 'Régimen Extracomunitario':
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
        country_code = self._get_sii_country_code()
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
    def _get_sii_exempt_cause(self, applied_taxes):
        """Código de la causa de exención según 3.6 y 3.7 de la FAQ del SII.

        :param applied_taxes: Taxes that are exempt for filtering the lines.
        """
        self.ensure_one()
        gen_type = self._get_sii_gen_type()
        if gen_type == 2:
            return 'E5'
        elif gen_type == 3:
            return 'E2'
        else:
            product_exempt_causes = self.mapped(
                'invoice_line_ids'
            ).filtered(lambda x: (
                any(tax in x.invoice_line_tax_ids for tax in applied_taxes) and
                x.product_id.sii_exempt_cause and
                x.product_id.sii_exempt_cause != 'none'
            )).mapped('product_id.sii_exempt_cause')
            product_exempt_causes = set(product_exempt_causes)
            if len(product_exempt_causes) > 1:
                raise exceptions.UserError(
                    _("Currently there's no support for multiple exempt "
                      "causes.")
                )
            if product_exempt_causes:
                return product_exempt_causes.pop()
            elif (self.fiscal_position_id.sii_exempt_cause and
                    self.fiscal_position_id.sii_exempt_cause != 'none'):
                return self.fiscal_position_id.sii_exempt_cause

    @api.multi
    def _get_no_taxable_cause(self):
        self.ensure_one()
        return self.fiscal_position_id.sii_no_taxable_cause or \
            'ImporteTAIReglasLocalizacion'

    def is_sii_invoice(self):
        """Hook method to be overridden in additional modules to verify
        if the invoice must be sended trough SII system, for special cases.

        :param self: Single invoice record
        :return: bool value indicating if the invoice should be sent to SII.
        """
        self.ensure_one()

    @api.multi
    def _get_sii_country_code(self):
        self.ensure_one()
        country_code = (
            self.partner_id.commercial_partner_id.country_id.code or
            (self.partner_id.vat or '')[:2]
        ).upper()
        return SII_COUNTRY_CODE_MAPPING.get(country_code, country_code)

    @api.depends('invoice_line_ids', 'invoice_line_ids.name', 'company_id',
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
                if invoice.invoice_line_ids:
                    if description:
                        description += ' | '
                    description += ' - '.join(
                        invoice.mapped('invoice_line_ids.name')
                    )
            invoice.sii_description = description[:500] or '/'

    @api.multi
    def _inverse_sii_description(self):
        for invoice in self:
            invoice.sii_manual_description = invoice.sii_description

    @api.multi
    @api.depends('company_id', 'company_id.sii_enabled',
                 'fiscal_position_id', 'fiscal_position_id.sii_active')
    def _compute_sii_enabled(self):
        """Compute if the invoice is enabled for the SII"""
        for invoice in self:
            if invoice.company_id.sii_enabled:
                invoice.sii_enabled = (
                    (invoice.fiscal_position_id and
                     invoice.fiscal_position_id.sii_active) or
                    not invoice.fiscal_position_id
                )
            else:
                invoice.sii_enabled = False

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(
            invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id,
        )
        sii_refund_type = self.env.context.get('sii_refund_type')
        supplier_invoice_number_refund = self.env.context.get(
            'supplier_invoice_number'
        )
        if sii_refund_type:
            res['sii_refund_type'] = sii_refund_type
        if supplier_invoice_number_refund:
            res['reference'] = supplier_invoice_number_refund
        return res

    @api.multi
    def _get_sii_sign(self):
        self.ensure_one()
        return -1.0 if self.sii_refund_type == 'I' and 'refund' in self.type \
            else 1.0

    @job(default_channel='root.invoice_validate_sii')
    @api.multi
    def confirm_one_invoice(self):
        self._send_invoice_to_sii()

    @job(default_channel='root.invoice_validate_sii')
    @api.multi
    def cancel_one_invoice(self):
        self._cancel_invoice_to_sii()
