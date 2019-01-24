# -*- coding: utf-8 -*-
# Copyright 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2012 NaN·Tic  (http://www.nan-tic.com)
# Copyright 2013 Acysos (http://www.acysos.com)
# Copyright 2013 Joaquín Pedrosa Gutierrez (http://gutierrezweb.es)
# Copyright 2016 - Tecnativa - Antonio Espinosa
# Copyright 2016 - Tecnativa - Angel Moya <odoo@tecnativa.com>
# Copyright 2014-2017 - Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models, api, exceptions, _

import re
from datetime import datetime
from calendar import monthrange
from openerp.addons.decimal_precision import decimal_precision as dp


class L10nEsAeatMod347Report(models.Model):
    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod347.report"
    _description = "AEAT 347 Report"
    _period_yearly = True
    _period_quarterly = False
    _period_monthly = False
    _aeat_number = '347'

    @api.multi
    @api.depends('partner_record_ids',
                 'partner_record_ids.amount',
                 'partner_record_ids.cash_amount',
                 'partner_record_ids.real_estate_transmissions_amount')
    def _compute_totals(self):
        """Calculates the total_* fields from the line values."""
        for record in self:
            record.total_partner_records = len(record.partner_record_ids)
            record.total_amount = sum(
                record.mapped('partner_record_ids.amount')
            )
            record.total_cash_amount = sum(
                record.mapped('partner_record_ids.cash_amount')
            )
            record.total_real_estate_transmissions_amount = sum(
                record.mapped(
                    'partner_record_ids.real_estate_transmissions_amount'
                )
            )

    @api.multi
    @api.depends('real_estate_record_ids',
                 'real_estate_record_ids.amount')
    def _compute_totals_real_estate(self):
        """Calculates the total_* fields from the line values."""
        for record in self:
            record.total_real_estate_records = len(
                record.real_estate_record_ids
            )
            record.total_real_estate_amount = sum(
                record.mapped('real_estate_record_ids.amount')
            )

    number = fields.Char(default='347')
    group_by_vat = fields.Boolean(
        string='Group by VAT number', oldname='group_by_cif')
    only_supplier = fields.Boolean(string='Only Suppliers')
    operations_limit = fields.Float(
        string='Invoiced Limit (1)', digits=(13, 2), default=3005.06,
        help="The declaration will include partners with the total of "
             "operations over this limit")
    received_cash_limit = fields.Float(
        string='Received cash Limit (2)', digits=(13, 2), default=6000.00,
        help="The declaration will show the total of cash operations over "
             "this limit")
    charges_obtp_limit = fields.Float(
        string='Charges on behalf of third parties Limit (3)', digits=(13, 2),
        help="The declaration will include partners from which we received "
             "payments, on behalf of third parties, over this limit",
        default=300.51)
    total_partner_records = fields.Integer(
        compute="_compute_totals", string="Partners records")
    total_amount = fields.Float(
        compute="_compute_totals", string="Amount")
    total_cash_amount = fields.Float(
        compute="_compute_totals", string="Cash Amount")
    total_real_estate_transmissions_amount = fields.Float(
        compute="_compute_totals", string="Real Estate Transmissions Amount",
        oldname='total_real_state_transmissions_amount')
    total_real_estate_records = fields.Integer(
        compute="_compute_totals_real_estate", string="Real estate records",
        oldname='total_real_state_records')
    total_real_estate_amount = fields.Float(
        compute="_compute_totals_real_estate", string="Real Estate Amount",
        oldname='total_real_state_amount')
    partner_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod347.partner_record',
        inverse_name='report_id', string='Partner Records')
    real_estate_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod347.real_estate_record',
        inverse_name='report_id', string='Real Estate Records',
        oldname='real_state_record_ids')

    @api.multi
    def button_confirm(self):
        """Different check out in report"""
        for item in self:
            # Browse partner record lines to check if all are correct (all
            # fields filled)
            partner_errors = []
            for partner_record in item.partner_record_ids:
                if not partner_record.check_ok:
                    partner_errors.append(
                        _("- %s (%s)") %
                        (partner_record.partner_id.name,
                         partner_record.partner_id.id))
            real_state_errors = []
            for real_estate_record in item.real_estate_record_ids:
                if not real_estate_record.check_ok:
                    real_state_errors.append(
                        _("- %s (%s)") %
                        (real_estate_record.partner_id.name,
                         real_estate_record.partner_id.id))
            error = _("Please review partner and real estate records, "
                      "some of them are in red color:\n\n")
            if partner_errors:
                error += _("Partner record errors:\n")
                error += '\n'.join(partner_errors)
                error += '\n\n'
            if real_state_errors:
                error += _("Real estate record errors:\n")
                error += '\n'.join(real_state_errors)
            if partner_errors or real_state_errors:
                raise exceptions.ValidationError(error)
        return super(L10nEsAeatMod347Report, self).button_confirm()

    @api.multi
    def btn_list_records(self):
        return {
            'domain': "[('report_id','in'," + str(self.ids) + ")]",
            'name': _("Partner records"),
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'l10n.es.aeat.mod347.partner_record',
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def calculate(self):
        for report in self:
            # Delete previous partner records
            report.partner_record_ids.unlink()
            partners = {}
            # Read invoices: normal and refunds
            # We have to call _invoices_search always first
            partners = report._invoices_search(partners)
            # Read cash movements
            partners = report._cash_moves_search(partners)
            for k, v in partners.iteritems():
                report._partner_records_create(v)
            report.partner_record_ids.calculate_quarter_totals()
            report.partner_record_ids.calculate_quarter_cash_totals()
        return True

    def _get_default_address(self, partner):
        """Get the default invoice address of the partner"""
        partner_obj = self.env['res.partner']
        address_ids = partner.address_get(['invoice', 'default'])
        if address_ids.get('invoice'):
            return partner_obj.browse(address_ids['invoice'])
        elif address_ids.get('default'):
            return partner_obj.browse(address_ids['default'])
        else:
            return None

    def _invoice_amount_get(self, invoices, refunds):
        invoice_amount = sum(invoices.mapped('amount_total_wo_irpf'))
        refund_amount = sum(refunds.mapped('amount_total_wo_irpf'))
        amount = invoice_amount - refund_amount
        if abs(amount) > self.operations_limit:
            return amount
        return 0

    def _cash_amount_get(self, moves):
        amount = sum([line.credit for line in moves])
        if abs(amount) > self.received_cash_limit:
            return amount
        return 0

    def _cash_moves_group(self, moves):
        cash_moves = {}
        # Group cash move lines by origin operation fiscalyear
        for move_line in moves:
            # FIXME: ugly group by reconciliation invoices, because there
            # isn't any direct relationship between payments and invoice
            invoices = []
            if move_line.reconcile_id:
                for line in move_line.reconcile_id.line_id:
                    if line.invoice:
                        invoices.append(line.invoice)
            elif move_line.reconcile_partial_id:
                for line in move_line.reconcile_partial_id.line_partial_ids:
                    if line.invoice:
                        invoices.append(line.invoice)
            # Remove duplicates
            invoices = list(set(invoices))
            if invoices:
                invoice = invoices[0]
                year = fields.Date.from_string(invoice.date_invoice).year
                if year not in cash_moves:
                    cash_moves[year] = move_line
                else:
                    cash_moves[year] |= move_line
        return cash_moves

    def _partner_record_a_create(self, data, vals):
        """Partner record type A: Adquisiciones de bienes y servicios

        Create from income (from supplier) invoices
        """
        partner_record_obj = self.env['l10n.es.aeat.mod347.partner_record']
        record = False
        vals['operation_key'] = 'A'
        invoices = data.get('in_invoices', self.env['account.invoice'])
        refunds = data.get('in_refunds', self.env['account.invoice'])
        amount = self._invoice_amount_get(invoices, refunds)
        if amount:
            vals['amount'] = amount
            vals['invoice_record_ids'] = [
                (0, 0, {'invoice_id': x})
                for x in (invoices.ids + refunds.ids)]
            record = partner_record_obj.create(vals)
        return record

    def _partner_record_b_create(self, data, vals):
        """Partner record type B: Entregas de bienes y servicios

        Create from outcome (from customer) invoices and cash movements
        """
        partner_record_obj = self.env['l10n.es.aeat.mod347.partner_record']
        cash_record_obj = self.env['l10n.es.aeat.mod347.cash_record']
        records = []
        invoice_record = False
        vals['operation_key'] = 'B'
        invoices = data.get('out_invoices', self.env['account.invoice'])
        refunds = data.get('out_refunds', self.env['account.invoice'])
        moves = data.get('cash_moves', self.env['account.move.line'])
        amount = self._invoice_amount_get(invoices, refunds)
        if amount:
            vals['amount'] = amount
            vals['invoice_record_ids'] = [
                (0, 0, {'invoice_id': x})
                for x in (invoices.ids + refunds.ids)]
            invoice_record = partner_record_obj.create(vals)
            if invoice_record:
                records.append(invoice_record)
        if self._cash_amount_get(moves):
            cash_moves = self._cash_moves_group(moves)
            for year in cash_moves.keys():
                amount = self._cash_amount_get(cash_moves[year])
                if amount:
                    if year != self.year or not invoice_record:
                        vals['amount'] = 0.0
                        vals['cash_amount'] = amount
                        vals['origin_year'] = year
                        partner_record = partner_record_obj.create(vals)
                        if partner_record:
                            records.append(partner_record)
                    else:
                        invoice_record.write({
                            'cash_amount': amount,
                            'origin_year': year,
                        })
                        partner_record = invoice_record
                    for line in cash_moves[year]:
                        cash_record_obj.create({
                            'partner_record_id': partner_record.id,
                            'move_line_id': line.id,
                            'date': line.date,
                            'amount': line.credit,
                        })
        return records

    def _partner_records_create(self, data):
        partner = data.get('partner')
        address = self._get_default_address(partner)
        partner_country_code, partner_vat = (
            re.match(r"([A-Z]{0,2})(.*)", partner.vat or '').groups())
        community_vat = ''
        if not partner_country_code:
            partner_country_code = address.country_id.code
        partner_state_code = address.state_id.code
        if partner_country_code != 'ES':
            partner_vat = ''
            community_vat = partner.vat
            partner_state_code = 99
        vals = {
            'report_id': self.id,
            'partner_id': partner.id,
            'partner_vat': partner_vat,
            'representative_vat': '',
            'community_vat': community_vat,
            'partner_state_code': partner_state_code,
            'partner_country_code': partner_country_code,
        }
        # Create A record
        self._partner_record_a_create(data, vals)
        # Create B records
        self._partner_record_b_create(data, vals)
        return True

    def _invoices_search(self, partners):
        invoice_obj = self.env['account.invoice']
        partner_obj = self.env['res.partner']
        domain = [
            ('state', 'in', ['open', 'paid']),
            ('date_invoice', '>=', self.date_start),
            ('date_invoice', '<=', self.date_end),
            ('not_in_mod347', '=', False),
            ('commercial_partner_id.not_in_mod347', '=', False),
        ]
        if self.only_supplier:
            domain.append(('type', 'in', ('in_invoice', 'in_refund')))
        key_field = 'id'
        if self.group_by_vat:
            key_field = 'vat'
        groups = invoice_obj.read_group(
            domain, ['commercial_partner_id'], ['commercial_partner_id'])
        for group in groups:
            partner = partner_obj.browse(group['commercial_partner_id'][0])
            key_value = partner[key_field]
            invoices = invoice_obj.search(group['__domain'])
            in_invoices = invoices.filtered(
                lambda x: x.type in 'in_invoice')
            in_refunds = invoices.filtered(
                lambda x: x.type in 'in_refund')
            out_invoices = invoices.filtered(
                lambda x: x.type in 'out_invoice')
            out_refunds = invoices.filtered(
                lambda x: x.type in 'out_refund')
            if key_value not in partners:
                partners[key_value] = {
                    # Get first partner found when grouping by vat
                    'partner': partner,
                    'in_invoices': in_invoices,
                    'in_refunds': in_refunds,
                    'out_invoices': out_invoices,
                    'out_refunds': out_refunds,
                }
            else:
                # No need to check here if *_invoices exists,
                # because this entry has been created in this method
                partners[key_value]['in_invoices'] += in_invoices
                partners[key_value]['in_refunds'] += in_refunds
                partners[key_value]['out_invoices'] += out_invoices
                partners[key_value]['out_refunds'] += out_refunds
        return partners

    def _cash_moves_search(self, partners):
        partner_obj = self.env['res.partner']
        move_line_obj = self.env['account.move.line']
        cash_journals = self.env['account.journal'].search(
            [('type', '=', 'cash')],
        )
        if not cash_journals or self.only_supplier:
            return partners
        domain = [
            ('account_id.internal_type', '=', 'receivable'),
            ('journal_id', 'in', cash_journals.ids),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('partner_id.not_in_mod347', '=', False),
        ]
        groups = move_line_obj.read_group(
            domain, ['partner_id'], ['partner_id'],
        )
        key_field = 'id'
        if self.group_by_vat:
            key_field = 'vat'
        for group in groups:
            partner = partner_obj.browse(group['partner_id'][0])
            key_value = partner[key_field]
            moves = move_line_obj.search(group['__domain'])
            if key_value not in partners:
                partners[key_value] = {
                    # Get first partner found when grouping by vat
                    'partner': partner,
                    'cash_moves': moves,
                }
            else:
                # Check here if cash_moves exists, maybe this entry
                # has been created by _invoices_search
                if partners[key_value].get('cash_moves'):
                    partners[key_value]['cash_moves'] += moves
                else:
                    partners[key_value]['cash_moves'] = moves
        return partners


class L10nEsAeatMod347PartnerRecord(models.Model):
    _name = 'l10n.es.aeat.mod347.partner_record'
    _description = 'Partner Record'
    _rec_name = "partner_vat"

    @api.model
    def _default_record_id(self):
        return self.env.context.get('report_id', False)

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod347.report', string='AEAT 347 Report',
        ondelete="cascade", default=_default_record_id,
    )
    operation_key = fields.Selection(
        selection=[
            ('A', u'A - Adquisiciones de bienes y servicios superiores al '
                  u'límite (1)'),
            ('B',
             u'B - Entregas de bienes y servicios superiores al límite (1)'),
            ('C',
             u'C - Cobros por cuenta de terceros superiores al límite (3)'),
            ('D', u'D - Adquisiciones efectuadas por Entidades Públicas '
                  u'(...) superiores al límite (1)'),
            ('E', u'E - Subvenciones, auxilios y ayudas satisfechas por Ad. '
                  u'Públicas superiores al límite (1)'),
            ('F', u'F - Ventas agencia viaje'),
            ('G', u'G - Compras agencia viaje'),
        ],
        string='Operation Key',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', required=True)
    partner_vat = fields.Char(string='VAT number', size=9)
    representative_vat = fields.Char(
        string='L.R. VAT number', size=9,
        help="Legal Representative VAT number")
    community_vat = fields.Char(
        string='Community vat number', size=17,
        help="VAT number for professionals established in other state "
             "member without national VAT")
    partner_country_code = fields.Char(string='Country Code', size=2)
    partner_state_code = fields.Char(string='State Code', size=2)
    first_quarter = fields.Float(
        string="First quarter operations", digits=dp.get_precision('Account'),
        help="Total amount of first quarter in, out and refund invoices "
             "for this partner", readonly=True,
    )
    first_quarter_real_estate_transmission_amount = fields.Float(
        string="First quarter real estate", digits=dp.get_precision('Account'),
        help="Total amount of first quarter real estate transmissions "
             "for this partner",
    )
    first_quarter_cash_amount = fields.Float(
        string="First quarter cash movements", readonly=True,
        digits=dp.get_precision('Account'),
        help="Total amount of first quarter cash movements for this partner",
    )
    second_quarter = fields.Float(
        string="Second quarter operations", digits=dp.get_precision('Account'),
        help="Total amount of second quarter in, out and refund invoices "
             "for this partner", readonly=True,
    )
    second_quarter_real_estate_transmission_amount = fields.Float(
        string="Second quarter real estate",
        digits=dp.get_precision('Account'),
        help="Total amount of second quarter real estate transmissions "
             "for this partner",
    )
    second_quarter_cash_amount = fields.Float(
        string="Second quarter cash movements", readonly=True,
        digits=dp.get_precision('Account'),
        help="Total amount of second quarter cash movements for this partner",
    )
    third_quarter = fields.Float(
        string="Third quarter operations", digits=dp.get_precision('Account'),
        help="Total amount of third quarter in, out and refund invoices "
             "for this partner", readonly=True,
    )
    third_quarter_real_estate_transmission_amount = fields.Float(
        string="Third quarter real estate", digits=dp.get_precision('Account'),
        help="Total amount of third quarter real estate transmissions "
             "for this partner",
    )
    third_quarter_cash_amount = fields.Float(
        string="Third quarter cash movements", readonly=True,
        digits=dp.get_precision('Account'),
        help="Total amount of third quarter cash movements for this partner",
    )
    fourth_quarter = fields.Float(
        string="Fourth quarter operations", digits=dp.get_precision('Account'),
        help="Total amount of fourth quarter in, out and refund invoices "
             "for this partner", readonly=True,
    )
    fourth_quarter_real_estate_transmission_amount = fields.Float(
        string="Fourth quarter real estate",
        digits=dp.get_precision('Account'),
        help="Total amount of fourth quarter real estate transmissions "
             "for this partner")
    fourth_quarter_cash_amount = fields.Float(
        string="Fourth quarter cash movements", readonly=True,
        digits=dp.get_precision('Account'),
        help="Total amount of fourth quarter cash movements for this partner",
    )
    amount = fields.Float(string='Operations amount', digits=(13, 2))
    cash_amount = fields.Float(string='Received cash amount', digits=(13, 2))
    real_estate_transmissions_amount = fields.Float(
        string='Real Estate Transmisions amount', digits=(13, 2),
    )
    insurance_operation = fields.Boolean(
        string='Insurance Operation',
        help="Only for insurance companies. Set to identify insurance "
             "operations aside from the rest.",
    )
    cash_basis_operation = fields.Boolean(
        string='Cash Basis Operation',
        help="Only for cash basis operations. Set to identify cash basis "
             "operations aside from the rest.",
    )
    tax_person_operation = fields.Boolean(
        string='Taxable Person Operation',
        help="Only for taxable person operations. Set to identify taxable "
             "person operations aside from the rest.",
    )
    related_goods_operation = fields.Boolean(
        string='Related Goods Operation',
        help="Only for related goods operations. Set to identify related "
             "goods operations aside from the rest.",
    )
    bussiness_real_estate_rent = fields.Boolean(
        string='Bussiness Real Estate Rent',
        help="Set to identify real estate rent operations aside from the rest."
             " You'll need to fill in the real estate info only when you are "
             "the one that receives the money.",
    )
    origin_year = fields.Integer(
        string='Origin year', help="Origin cash operation year",
    )
    invoice_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod347.invoice_record',
        inverse_name='partner_record_id', string='Invoice records',
    )
    real_estate_record_ids = fields.Many2many(
        compute="_compute_real_estate_record_ids",
        comodel_name="l10n.es.aeat.mod347.real_estate_record",
        string='Real Estate Records',
    )
    cash_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod347.cash_record',
        inverse_name='partner_record_id', string='Payment records',
    )
    check_ok = fields.Boolean(
        compute="_compute_check_ok", string='Record is OK',
        store=True, readonly=True, help='Checked if this record is OK',
    )

    @api.multi
    def _compute_real_estate_record_ids(self):
        """Get the real estate records from this record parent report for this
        partner.
        """
        self.real_estate_record_ids = self.env[
            'l10n.es.aeat.mod347.real_estate_record']
        if self.partner_id:
            self.real_estate_record_ids = self.real_estate_record_ids.search(
                [('report_id', '=', self.report_id.id),
                 ('partner_id', '=', self.partner_id.id)]
            )

    @api.multi
    @api.depends('partner_country_code', 'partner_state_code', 'partner_vat',
                 'community_vat')
    def _compute_check_ok(self):
        for record in self:
            record.check_ok = (
                record.partner_country_code and
                record.partner_state_code and
                record.partner_state_code.isdigit() and
                (record.partner_vat or record.partner_country_code != 'ES')
            )

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """Loads some partner data (country, state and vat) when the selected
        partner changes.
        """
        if self.partner_id:
            addr = self.partner_id.address_get(['delivery', 'invoice'])
            # Get the invoice or the default address of the partner
            addr = self.partner_id.address_get(['invoice', 'default'])
            address = self.env['res.partner'].browse(addr['invoice'])
            self.partner_vat = self.partner_id.vat and \
                re.match("(ES){0,1}(.*)",
                         self.partner_id.vat).groups()[1]
            self.partner_state_code = address.state_id.code
            self.partner_country_code = address.country_id.code
        else:
            self.partner_vat = ''
            self.partner_country_code = ''
            self.partner_state_code = ''

    @api.multi
    @api.depends('invoice_record_ids.invoice_id.date', 'report_id.year')
    def calculate_quarter_totals(self):

        def calc_amount_by_quarter(invoices, refunds, year, month_start):
            day_start = 1
            month_end = month_start + 2
            day_end = monthrange(year, month_end)[1]
            date_start = fields.Date.to_string(
                datetime(year, month_start, day_start)
            )
            date_end = fields.Date.to_string(
                datetime(year, month_end, day_end)
            )
            return (
                sum(invoices.filtered(
                    lambda x: date_start <= x.invoice_id.date <= date_end
                ).mapped('amount')) - sum(refunds.filtered(
                    lambda x: date_start <= x.invoice_id.date <= date_end
                ).mapped('amount'))
            )

        for record in self:
            year = record.report_id.year
            invoices = record.invoice_record_ids.filtered(
                lambda rec: (
                    rec.invoice_id.type in ('out_invoice', 'in_invoice')
                )
            )
            refunds = record.invoice_record_ids.filtered(
                lambda rec: (
                    rec.invoice_id.type in ('out_refund', 'in_refund')
                )
            )
            record.first_quarter = calc_amount_by_quarter(
                invoices, refunds, year, 1,
            )
            record.second_quarter = calc_amount_by_quarter(
                invoices, refunds, year, 4,
            )
            record.third_quarter = calc_amount_by_quarter(
                invoices, refunds, year, 7,
            )
            record.fourth_quarter = calc_amount_by_quarter(
                invoices, refunds, year, 10,
            )

    @api.multi
    def calculate_quarter_cash_totals(self):
        def calc_amount_by_quarter(records, year, month_start):
            day_start = 1
            month_end = month_start + 2
            day_end = monthrange(year, month_end)[1]
            date_start = fields.Date.to_string(
                datetime(year, month_start, day_start)
            )
            date_end = fields.Date.to_string(
                datetime(year, month_end, day_end)
            )
            return sum(records.filtered(
                lambda x: date_start <= x.invoice_id.date <= date_end
            ).mapped('amount'))

        for record in self:
            if not record.cash_record_ids:
                continue
            year = record.report_id.year
            record.first_quarter_cash_amount = calc_amount_by_quarter(
                record.cash_record_ids, year, 1,
            )
            record.second_quarter_cash_amount = calc_amount_by_quarter(
                record.cash_record_ids, year, 4,
            )
            record.third_quarter_cash_amount = calc_amount_by_quarter(
                record.cash_record_ids, year, 7,
            )
            record.fourth_quarter_cash_amount = calc_amount_by_quarter(
                record.cash_record_ids, year, 10,
            )
            # Totals
            record.cash_amount = sum([
                record.first_quarter_cash_amount,
                record.second_quarter_cash_amount,
                record.third_quarter_cash_amount,
                record.fourth_quarter_cash_amount
            ])


class L10nEsAeatMod347RealStateRecord(models.Model):
    _name = 'l10n.es.aeat.mod347.real_estate_record'
    _description = 'Real Estate Record'
    _rec_name = "reference"

    @api.model
    def _default_record_id(self):
        return self.env.context.get('report_id', False)

    @api.model
    def _default_partner_id(self):
        return self.env.context.get('partner_id', False)

    @api.model
    def _default_partner_vat(self):
        return self.env.context.get('partner_vat', False)

    @api.model
    def _default_representative_vat(self):
        return self.env.context.get('representative_vat', False)

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod347.report', string='AEAT 347 Report',
        ondelete="cascade", index=1, default=_default_record_id,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', required=True,
        default=_default_partner_id,
    )
    partner_vat = fields.Char(
        string='VAT number', size=32, default=_default_partner_vat,
    )
    representative_vat = fields.Char(
        string='L.R. VAT number', size=32, default=_default_representative_vat,
        help="Legal Representative VAT number")
    amount = fields.Float(string='Amount', digits=(13, 2))
    situation = fields.Selection(
        selection=[('1', '1 - Spain but Basque Country and Navarra'),
                   ('2', '2 - Basque Country and Navarra'),
                   ('3', '3 - Spain, without catastral reference'),
                   ('4', '4 - Foreign')],
        string='Real estate Situation')
    reference = fields.Char(
        string='Catastral Reference', size=25)
    address_type = fields.Char(
        string='Address type', size=5)
    address = fields.Char(string='Address', size=50)
    number_type = fields.Selection(
        selection=[('NUM', 'Number'),
                   ('KM.', 'Kilometer'),
                   ('S/N', 'Without number')],
        string='Number type')
    number = fields.Integer(string='Number', size=5)
    number_calification = fields.Selection(
        selection=[('BIS', 'Bis'),
                   ('MOD', 'Mod'),
                   ('DUP', 'Dup'),
                   ('ANT', 'Ant')],
        string='Number calification')
    block = fields.Char(string='Block', size=3)
    portal = fields.Char(string='Portal', size=3)
    stairway = fields.Char(string='Stairway', size=3)
    floor = fields.Char(string='Floor', size=3)
    door = fields.Char(string='Door', size=3)
    complement = fields.Char(
        string='Complement', size=40,
        help="Complement (urbanization, industrial park...)")
    city = fields.Char(string='City', size=30)
    township = fields.Char(string='Township', size=30)
    township_code = fields.Char(string='Township Code', size=5)
    state_code = fields.Char(string='State Code', size=2)
    postal_code = fields.Char(string='Postal code', size=5)
    check_ok = fields.Boolean(
        compute="_compute_check_ok", string='Record is OK',
        store=True, help='Checked if this record is OK',
    )

    @api.multi
    @api.depends('state_code')
    def _compute_check_ok(self):
        for record in self:
            record.check_ok = bool(record.state_code)

    @api.onchange('partner_id')
    def on_change_partner_id(self):
        """Loads some partner data (vat) when the selected partner changes."""
        if self.partner_id:
            self.partner_vat = re.match("(ES){0,1}(.*)",
                                        self.partner_id.vat).groups()[1]
        else:
            self.partner_vat = ''


class L10nEsAeatMod347InvoiceRecord(models.Model):
    _name = 'l10n.es.aeat.mod347.invoice_record'
    _description = 'Invoice Record'

    @api.model
    def _default_partner_record(self):
        return self.env.context.get('partner_record_id', False)

    partner_record_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod347.partner_record',
        string='Partner record', required=True, ondelete="cascade", select=1,
        default=_default_partner_record)
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Invoice', required=True,
        ondelete="cascade")
    invoice_type = fields.Selection(
        related="invoice_id.type", readonly=True, store=True,
    )
    date = fields.Date(
        string='Date', related='invoice_id.date_invoice', store=True,
        readonly=True,
    )
    amount = fields.Float(
        string='Amount', related="invoice_id.amount_total_wo_irpf", store=True,
        readonly=True,
    )


class L10nEsAeatMod347CashRecord(models.Model):
    """Represents a payment record."""
    _name = 'l10n.es.aeat.mod347.cash_record'
    _description = 'Cash Record'

    @api.model
    def _default_partner_record(self):
        return self.env.context.get('partner_record_id', False)

    partner_record_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod347.partner_record',
        string='Partner record', required=True, ondelete="cascade", select=1,
        default=_default_partner_record)
    move_line_id = fields.Many2one(
        comodel_name='account.move.line', string='Account move line',
        required=True, ondelete="cascade")
    date = fields.Date(string='Date')
    amount = fields.Float(string='Amount')
