# Copyright 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2012 NaN·Tic  (http://www.nan-tic.com)
# Copyright 2013 Acysos (http://www.acysos.com)
# Copyright 2013 Joaquín Pedrosa Gutierrez (http://gutierrezweb.es)
# Copyright 2016 - Tecnativa - Antonio Espinosa
# Copyright 2016 - Tecnativa - Angel Moya <odoo@tecnativa.com>
# Copyright 2014-2017 - Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2018 - PESOL - Angel Moya <info@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, exceptions, _

import re
from datetime import datetime
from calendar import monthrange
import odoo.addons.decimal_precision as dp


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

    def _account_move_line_domain(self, taxes):
        """Return domain for searching move lines.

        :param: taxes: Taxes to look for in move lines.
        """
        return [('partner_id.not_in_mod347', '=', False),
                ('invoice_id.not_in_mod347', '=', False),
                ('move_id.force_not_in_mod347', '=', False),
                ('date', '>=', self.date_start),
                ('date', '<=', self.date_end),
                '|',
                ('tax_ids', 'in', taxes.ids),
                ('tax_line_id', 'in', taxes.ids),
                ]

    @api.model
    def _get_taxes(self, map):
        tax_obj = self.env['account.tax']
        # Obtain all the taxes to be considered
        tax_templates = map.mapped('tax_ids').mapped('description')
        if not tax_templates:
            raise exceptions.Warning(_('No Tax Mapping was found'))
        # search the account.tax referred to by the template
        taxes = tax_obj.search(
            [('description', 'in', tax_templates),
             ('company_id', 'child_of', self.company_id.id)])
        return taxes

    def _create_partner_records(self, key, map_ref):
        map = self.env.ref(map_ref)
        taxes = self._get_taxes(map)
        domain = self._account_move_line_domain(taxes)
        records = self.env['account.move.line'].read_group(
            domain,
            ['partner_id', 'balance'],
            ['partner_id']
        )
        if map_ref == 'l10n_es_aeat_mod347.aeat_mod347_map_a':
            filtered_records = list(filter(
                lambda d: d['balance'] > self.operations_limit, records)
            )
        else:
            filtered_records = list(filter(
                lambda d: d['balance'] < (-1 * self.operations_limit), records)
            )
        filtered_partners = [
            record['partner_id'][0] for record in filtered_records]
        domain.append(['partner_id', 'in', filtered_partners])
        records = self.env['account.move.line'].read_group(
            domain,
            ['partner_id', 'move_id',
             'balance', 'debit', 'credit'],
            ['partner_id', 'move_id']
        )
        partner_obj = self.env['res.partner']
        for record in records:
            partner = partner_obj.browse(record['partner_id'][0])
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
            partner_record_obj = self.env[
                'l10n.es.aeat.mod347.partner_record']
            vals['operation_key'] = key
            amount = record['balance']
            if amount:
                vals['amount'] = abs(amount)
                move_lines = self.env['account.move.line'].read_group(
                    record['__domain'],
                    ['move_id', 'balance'],
                    record['__context']['group_by']
                )
                vals['move_record_ids'] = [
                    (0, 0, {'move_id': move_line['move_id'][0],
                            'amount': abs(move_line['balance'])})
                    for move_line in move_lines]
                partner_record_obj.create(vals)

    def _create_cash_moves(self):
        partner_obj = self.env['res.partner']
        move_line_obj = self.env['account.move.line']
        cash_journals = self.env['account.journal'].search(
            [('type', '=', 'cash')],
        )
        if not self.only_supplier or cash_journals:

            domain = [
                ('account_id.internal_type', '=', 'receivable'),
                ('journal_id', 'in', cash_journals.ids),
                ('date', '>=', self.date_start),
                ('date', '<=', self.date_end),
                ('partner_id.not_in_mod347', '=', False),
            ]
            partner_cash = move_line_obj.read_group(
                domain,
                ['partner_id',
                 'balance', 'debit', 'credit'],
                ['partner_id']
            )
            partner_obj = self.env['res.partner']
            for partner_data in partner_cash:
                partner = partner_obj.browse(partner_data['partner_id'][0])
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
                partner_record_obj = self.env[
                    'l10n.es.aeat.mod347.partner_record']
                vals['operation_key'] = 'C'
                amount = partner_data['balance']
                if amount:
                    vals['amount'] = abs(amount)
                    move_lines = self.env['account.move.line'].search(
                        partner_data['__domain']
                    ).read(
                        ['id', 'balance', 'date'])
                    vals['cash_record_ids'] = [
                        (0, 0, {'move_line_id': move_line['id'],
                                'amount': abs(move_line['balance']),
                                'date': move_line['date']})
                        for move_line in move_lines]
                    partner_record_obj.search([
                        ('partner_id', '=', partner.id),
                        ('type', '=', 'B')
                    ])
                    partner_record_obj.create(vals)

    @api.multi
    def calculate(self):
        for report in self:
            # Delete previous partner records
            report.partner_record_ids.unlink()

            self._create_partner_records(
                'A', 'l10n_es_aeat_mod347.aeat_mod347_map_a')
            self._create_partner_records(
                'B', 'l10n_es_aeat_mod347.aeat_mod347_map_b')
            self._create_cash_moves()

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


class L10nEsAeatMod347PartnerRecord(models.Model):
    _name = 'l10n.es.aeat.mod347.partner_record'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Partner Record'
    _rec_name = "partner_vat"

    @api.model
    def _default_record_id(self):
        return self.env.context.get('report_id', False)

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod347.report', string='AEAT 347 Report',
        ondelete="cascade", default=_default_record_id,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesperson',
        track_visibility='onchange',
        default=lambda self: self.env.user,
        copy=False)
    state = fields.Selection(
        [('pending', 'Pending'),
         ('sended', 'Sended'),
         ('confirmed', 'Confirmed'),
         ('exception', 'Exception'),
         ],
        default='pending',
        string='State')
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
    move_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod347.move.record',
        inverse_name='partner_record_id', string='Move records',
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
    @api.depends('move_record_ids.move_id.date', 'report_id.year')
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
                    lambda x: date_start <= x.move_id.date <= date_end
                ).mapped('amount')) - sum(refunds.filtered(
                    lambda x: date_start <= x.move_id.date <= date_end
                ).mapped('amount'))
            )

        for record in self:
            year = record.report_id.year
            invoices = record.move_record_ids.filtered(
                lambda rec: (
                    rec.move_id.move_type in ('receivable', 'payable')
                )
            )
            refunds = record.move_record_ids.filtered(
                lambda rec: (
                    rec.move_id.move_type in (
                        'receivable_refund', 'payable_refund')
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
                lambda x: date_start <= x.move_line_id.date <= date_end
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

    @api.multi
    def action_exception(self):
        self.write({'state': 'exception'})

    @api.multi
    def action_confirm(self):
        self.write({'state': 'confirmed'})

    @api.multi
    def action_send(self):
        self.write({'state': 'sended'})
        self.ensure_one()
        template = self.env.ref(
            'l10n_es_aeat_mod347.email_template_347', False)
        compose_form = self.env.ref(
            'mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='l10n.es.aeat.mod347.partner_record',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            force_email=True
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def send_email_direct(self):
        Mail = self.env['mail.compose.message']
        for record in self:
            wiz = record.action_send()
            mail = Mail.with_context(wiz.get('context')).create({})
            # TODO: correct template load.
            # onchange_template_id(
            #    self, template_id, composition_mode, model, res_id)
            mail.send_mail_action()

    @api.multi
    def action_pending(self):
        self.write({'state': 'pending'})


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


class L10nEsAeatMod347MoveRecord(models.Model):
    _name = 'l10n.es.aeat.mod347.move.record'
    _description = 'Move Record'

    @api.model
    def _default_partner_record(self):
        return self.env.context.get('partner_record_id', False)

    partner_record_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod347.partner_record',
        string='Partner record', required=True, ondelete="cascade", index=True,
        default=_default_partner_record)
    move_id = fields.Many2one(
        comodel_name='account.move', string='Move', required=True,
        ondelete="cascade")

    date = fields.Date(
        string='Date', related='move_id.date', store=True,
        readonly=True,
    )
    amount = fields.Float(
        string='Amount',
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
        string='Partner record', required=True, ondelete="cascade", index=True,
        default=_default_partner_record)
    move_line_id = fields.Many2one(
        comodel_name='account.move.line', string='Account move line',
        required=True, ondelete="cascade")
    date = fields.Date(string='Date')
    amount = fields.Float(string='Amount')
