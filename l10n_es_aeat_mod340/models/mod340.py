# -*- coding: utf-8 -*-
# Copyright 2011 - Ting (http://www.ting.es)
# Copyright 2012 - Acysos S.L. (http://acysos.com)
#                - Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2011 - NaN Projectes de Programari Lliure, S.L.
#                - http://www.NaN-tic.com
# Copyright 2016 - Tecnativa - Angel Moya <odoo@tecnativa.com>
# Copyright 2017 - Aselcis Consulting (http://www.aselcis.com)
#                - Miguel Paraíso <miguel.paraiso@aselcis.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api, fields, _
from odoo.exceptions import Warning
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import re


class L10nEsAeatMod340Report(models.Model):
    _inherit = "l10n.es.aeat.report"
    _name = 'l10n.es.aeat.mod340.report'
    _description = 'Model 340'
    _aeat_number = '340'

    def _get_export_conf(self):
        try:
            return self.env.ref('l10n_es_aeat_mod340.aeat_mod340_main_export_config').id
        except ValueError:
            return self.env['aeat.model.export.config']

    name = fields.Char(
        compute='_compute_name',
        string="Name")
    export_config_id = fields.Many2one(
        comodel_name='aeat.model.export.config',
        oldname='export_config',
        string="Export configuration",
        default=_get_export_conf)
    issued_ids = fields.One2many(
        'l10n.es.aeat.mod340.issued',
        'mod340_id',
        string='Invoices Issued',
        states={'done': [('readonly', True)]})
    issued_tax_line_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod340.tax_line_issued',
        inverse_name='mod340_id',
        string='Issued Tax Lines')
    received_ids = fields.One2many(
        'l10n.es.aeat.mod340.received',
        'mod340_id',
        string='Invoices Received',
        states={'done': [('readonly', True)]})
    received_tax_line_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod340.tax_line_received',
        inverse_name='mod340_id',
        string='Received Tax Lines')
    investment_ids = fields.One2many(
        'l10n.es.aeat.mod340.investment',
        'mod340_id',
        string='Property Investment')
    ean13 = fields.Char(
        string='Electronic Code VAT reverse charge')
    total_taxable = fields.Float(
        compute='_get_number_records',
        string='Total Taxable',
        multi='recalc',
        help="The declaration will include partners with the total of operations over this limit")
    total_sharetax = fields.Float(
        compute='_get_number_records',
        string='Total Share Tax',
        multi='recalc',
        help="The declaration will include partners with the total of operations over this limit")
    number_records = fields.Integer(
        compute='_get_number_records',
        string='Records',
        multi='recalc',
        help="The declaration will include partners with the total of operations over this limit")
    total = fields.Float(
        compute='_get_number_records',
        string="Total",
        multi='recalc',
        help="The declaration will include partners with the total of operations over this limit")
    total_taxable_rec = fields.Float(
        compute='_get_number_records',
        string='Total Taxable', multi='recalc',
        help="The declaration will include partners with the total of operations over this limit")
    total_sharetax_rec = fields.Float(
        compute='_get_number_records',
        method=True,
        type='float', string='Total Share Tax', multi='recalc',
        help="The declaration will include partners with the total of operations over this limit")
    total_rec = fields.Float(
        compute='_get_number_records',
        string="Total",
        multi='recalc',
        help="The declaration will include partners with the total of operations over this limit")
    calculation_date = fields.Date(
        string='Calculation date',
        readonly=True)

    _defaults = {
        'number': '340',
    }

    def __init__(self, pool, cr):
        self._aeat_number = '340'
        super(L10nEsAeatMod340Report, self).__init__(pool, cr)

    @api.multi
    def calculate(self):
        account_invoice = self.env['account.invoice']
        invoices340 = self.env['l10n.es.aeat.mod340.issued']
        invoices340_rec = self.env['l10n.es.aeat.mod340.received']
        issued_obj = self.env['l10n.es.aeat.mod340.tax_line_issued']
        received_obj = self.env['l10n.es.aeat.mod340.tax_line_received']

        for report in self:
            if not report.company_id.partner_id.vat:
                raise Warning(_("Company [%s] don't have NIF") % report.company_id.partner_id.name)
            # Delete previous records
            report.issued_ids.unlink()
            report.received_ids.unlink()
            report.investment_ids.unlink()

            domain = [
                ('date', '>=', report.date_start),
                ('date', '<=', report.date_end),
            ]

            for invoice in account_invoice.search(domain):
                include = False
                for tax_line in invoice.tax_line_ids:
                    if tax_line.tax_id and tax_line.base:
                        if tax_line.tax_id.mod340:
                            include = True
                            break
                if include:
                    if invoice.partner_id.vat_type == '1':
                        if not invoice.partner_id.vat:
                            raise Warning(_("Partner [%s] don't have NIF") % invoice.partner_id.name)
                    if invoice.partner_id.vat:
                        country_code, nif = (re.match(r"([A-Z]{0,2})(.*)", invoice.partner_id.vat).groups())
                    else:
                        country_code = False
                        nif = False
                    values = {
                        'mod340_id': report.id,
                        'partner_id': invoice.partner_id.id,
                        'partner_vat': nif,
                        'representative_vat': '',
                        'partner_country_code': country_code,
                        'invoice_id': invoice.id,
                        'date_invoice': invoice.date_invoice,
                    }
                    sign = 1
                    if invoice.type in ['out_refund', 'in_refund']:
                        sign = -1
                    if invoice.type in ['out_invoice', 'out_refund']:
                        invoice_created = invoices340.create(values)
                    if invoice.type in ['in_invoice', 'in_refund']:
                        values['invoice_reference'] = invoice.reference
                        invoice_created = invoices340_rec.create(values)
                    tot_base_amount = 0
                    tot_tax_invoice = 0
                    # Add the invoices detail to the partner record
                    latest_tax_id = 0
                    for tax_line in invoice.tax_line_ids:
                        if tax_line.tax_id and tax_line.base:
                            if tax_line.tax_id != latest_tax_id:
                                latest_tax_id = tax_line.tax_id
                            else:
                                break
                            if tax_line.tax_id.mod340:
                                tax_percentage = tax_line.amount / tax_line.base
                                values = {
                                    'name': tax_line.name,
                                    'tax_percentage': tax_percentage,
                                    'tax_amount': tax_line.amount * sign,
                                    'base_amount': tax_line.base * sign,
                                    'invoice_record_id': invoice_created.id,
                                }
                                if invoice.type in ['out_invoice', 'out_refund']:
                                    issued_obj.create(values)
                                if invoice.type in ['in_invoice', 'in_refund']:
                                    received_obj.create(values)
                                tot_base_amount += tax_line.base * sign
                                tot_tax_invoice += tax_line.amount * sign

                    if invoice.type in ['out_invoice', 'out_refund']:
                        invoice_created.write({
                            'base_tax': tot_base_amount,
                            'amount_tax': tot_tax_invoice,
                            'total': tot_base_amount + tot_tax_invoice,
                        })
                    elif invoice.type in ['in_invoice', 'in_refund']:
                        invoice_created.write({
                            'base_tax': tot_base_amount,
                            'amount_tax': tot_tax_invoice,
                            'total': tot_base_amount + tot_tax_invoice,
                        })

            report.write({
                'state': 'calculated',
                'calculation_date':
                    time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            })

    @api.multi
    def _compute_name(self):
        """Returns the report name"""
        for report in self:
            report.name = report.number

    @api.multi
    def _get_number_records(self):
        for model in self:
            number_records = 0
            total_taxable = 0.0
            total_sharetax = 0.0
            total = 0.0
            total_taxable_rec = 0.0
            total_sharetax_rec = 0.0
            total_rec = 0.0
            for issue in model.issued_ids:
                number_records += len(issue.tax_line_ids)
                total_taxable += issue.base_tax
                total_sharetax += issue.amount_tax
                total += issue.base_tax + issue.amount_tax
            for issue in model.received_ids:
                number_records += len(issue.tax_line_ids)
                total_taxable_rec += issue.base_tax
                total_sharetax_rec += issue.amount_tax
                total_rec += issue.base_tax
                total_rec += issue.amount_tax
            self.number_records = number_records
            self.total_taxable = total_taxable
            self.total_sharetax = total_sharetax
            self.total = total
            self.total_taxable_rec = total_taxable_rec
            self.total_sharetax_rec = total_sharetax_rec
            self.total_rec = total_rec


class L10nEsAeatMod340Issued(models.Model):
    _name = 'l10n.es.aeat.mod340.issued'
    _description = 'Invoices invoice'
    _order = 'date_invoice asc, invoice_id asc'

    mod340_id = fields.Many2one(
        'l10n.es.aeat.mod340.report',
        string='Model 340',
        ondelete="cascade")
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        ondelete="cascade")
    partner_vat = fields.Char(
        string='Company CIF / NIF',
        size=9)
    representative_vat = fields.Char(
        string='L.R. VAT number',
        size=7,
        help="Legal Representative VAT number")
    partner_country_code = fields.Char(
        string='Country Code',
        size=2)
    invoice_id = fields.Many2one(
        'account.invoice',
        string='Invoice',
        ondelete="cascade")
    base_tax = fields.Float(
        string='Base tax bill',
        digits=(13, 2))
    amount_tax = fields.Float(
        string='Total tax',
        digits=(13, 2))
    total = fields.Float(
        string='Total',
        digits=(13, 2))
    tax_line_ids = fields.One2many(
        'l10n.es.aeat.mod340.tax_line_issued',
        'invoice_record_id',
        string='Tax lines')
    date_invoice = fields.Date(
        string='Date Invoice',
        readonly=True)

    country_vat = fields.Char(
        string='Country VAT',
        compute='_compute_country_vat')
    operation_key = fields.Char(
        string='Operation Key',
        compute='_compute_operation_key')
    invoice_date = fields.Char(
        string='Invoice Date',
        compute='_compute_invoice_date')
    invoice_qty = fields.Integer(
        string='Invoice Qty',
        compute='_compute_invoice_qty')
    cumulated_interval = fields.Char(
        string='Cumulated Interval',
        compute='_compute_cumulated_interval')

    base_cost = fields.Float(
        string='Base Cost')
    register_sequence = fields.Integer(
        string='Register Sequence')
    surcharge = fields.Integer(
        string='Surcharge')
    surcharge_fee = fields.Integer(
        string='Surcharge Fee')

    @api.multi
    def _compute_country_vat(self):
        extport_to_boe = self.env['l10n.es.aeat.report.export_to_boe']
        for record in self:
            text = ''
            if record.partner_country_code != 'ES':
                text += extport_to_boe._formatString(
                    record.partner_country_code, 2)
                text += extport_to_boe._formatString(record.partner_vat, 15)
            else:
                text += 17 * ' '
            record.country_vat = text

    @api.multi
    def _compute_operation_key(self):
        for record in self:
            if record.invoice_id:
                if record.invoice_id.origin_invoices_ids:
                    record.operation_key = 'D'
                elif len(record.tax_line_ids) > 1:
                    record.operation_key = 'C'
                elif record.invoice_id.is_ticket_summary:
                    record.operation_key = 'B'
            elif record.account_move_id:
                record.operation_key = record.account_move_id.mod340_operation_key
            else:
                record.operation_key = ' '

    @api.multi
    def _compute_invoice_date(self):
        for record in self:
            if record.invoice_id:
                record.invoice_date = fields.Date.from_string(
                    record.invoice_id.date_invoice).strftime("%Y%m%d")
            elif record.account_move_id:
                record.invoice_date = fields.Date.from_string(
                    record.account_move_id.date).strftime("%Y%m%d")

    @api.multi
    def _compute_invoice_qty(self):
        for record in self:
            if record.invoice_id.is_ticket_summary:
                record.invoice_qty = record.invoice_id.number_tickets
            else:
                record.invoice_qty = 1

    @api.multi
    def _compute_cumulated_interval(self):
        extport_to_boe = self.env['l10n.es.aeat.report.export_to_boe']
        for record in self:
            if record.invoice_id.is_ticket_summary == 1:
                text = extport_to_boe._formatString(
                    record.invoice_id.first_ticket, 40)
                text += extport_to_boe._formatString(
                    record.invoice_id.last_ticket, 40)
            else:
                text += 80 * ' '
            record.cumulated_interval = text


class L10nEsAeatMod340Received(models.Model):
    _name = 'l10n.es.aeat.mod340.received'
    _description = 'Invoices Received'
    _inherit = 'l10n.es.aeat.mod340.issued'

    tax_line_ids = fields.One2many(
        'l10n.es.aeat.mod340.tax_line_received',
        'invoice_record_id',
        string='Tax lines')
    invoice_reference = fields.Char(
        string='Invoice reference')
    deductible_fee = fields.Float(
        string='Deductible Fee')
    paid_amount = fields.Float(
        string='Paid Amount')
    pay_date = fields.Char(
        string='field_name')


class L10nEsAeatMod340Investment(models.Model):
    _name = 'l10n.es.aeat.mod340.investment'
    _description = 'Property Investment'
    _inherit = 'l10n.es.aeat.mod340.issued'


class L10nEsAeatMod340Intracommunity(models.Model):
    _name = 'l10n.es.aeat.mod340.intracommunity'
    _description = 'Intra-Community Operations '
    _inherit = 'l10n.es.aeat.mod340.issued'


class L10nEsAeatMod340TaxLineIssued(models.Model):
    _name = 'l10n.es.aeat.mod340.tax_line_issued'
    _description = 'Mod340 vat lines issued'

    name = fields.Char(
        string='Name',
        size=128,
        required=True,
        index=True)
    tax_percentage = fields.Float(
        string='Tax percentage',
        digits=(0, 4))
    tax_amount = fields.Float(
        string='Tax amount',
        digits=(13, 2))
    base_amount = fields.Float(
        string='Base tax bill',
        digits=(13, 2))
    invoice_record_id = fields.Many2one(
        'l10n.es.aeat.mod340.issued',
        string='Invoice issued',
        required=True,
        ondelete="cascade",
        index=True)

    mod340_id = fields.Many2one(
        'l10n.es.aeat.mod340.report',
        string='Model 340',
        ondelete="cascade",
        related='invoice_record_id.mod340_id',
        store=True)


class L10nEsAeatMod340TaxLineReceived(models.Model):
    _name = 'l10n.es.aeat.mod340.tax_line_received'
    _description = 'Mod340 vat lines received'
    _inherit = 'l10n.es.aeat.mod340.tax_line_issued'

    invoice_record_id = fields.Many2one(
        'l10n.es.aeat.mod340.received',
        string='Invoice received',
        required=True,
        ondelete="cascade",
        index=True)

    mod340_id = fields.Many2one(
        'l10n.es.aeat.mod340.report',
        string='Model 340',
        ondelete="cascade",
        related='invoice_record_id.mod340_id',
        store=True)
