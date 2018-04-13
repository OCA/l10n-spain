# -*- coding: utf-8 -*-
# Copyright 2004-2011 Pexego Sistemas Informáticos - Luis Manuel Angueira
# Copyright 2013 - Acysos S.L. - Ignacio Ibeas (Migración a v7)
# Copyright 2014-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from calendar import monthrange
from odoo import _, api, fields, exceptions, models
from odoo.tools import config
from datetime import datetime


class L10nEsAeatReport(models.AbstractModel):
    _name = "l10n.es.aeat.report"
    _description = "AEAT report base module"
    _rec_name = 'name'
    _aeat_number = False
    _period_quarterly = True
    _period_monthly = True
    _period_yearly = False

    def _default_company_id(self):
        company_obj = self.env['res.company']
        return company_obj._company_default_get('l10n.es.aeat.report')

    def _default_journal(self):
        return self.env['account.journal'].search(
            [('type', '=', 'general')])[:1]

    def get_period_type_selection(self):
        period_types = []
        if self._period_yearly or config['test_enable']:
            period_types += [('0A', '0A - Anual')]
        if self._period_quarterly:
            period_types += [('1T', '1T - Primer trimestre'),
                             ('2T', '2T - Segundo trimestre'),
                             ('3T', '3T - Tercer trimestre'),
                             ('4T', '4T - Cuarto trimestre')]
        if self._period_monthly or config['test_enable']:
            period_types += [('01', '01 - Enero'),
                             ('02', '02 - Febrero'),
                             ('03', '03 - Marzo'),
                             ('04', '04 - Abril'),
                             ('05', '05 - Mayo'),
                             ('06', '06 - Junio'),
                             ('07', '07 - Julio'),
                             ('08', '08 - Agosto'),
                             ('09', '09 - Septiembre'),
                             ('10', '10 - Octubre'),
                             ('11', '11 - Noviembre'),
                             ('12', '12 - Diciembre')]
        return period_types

    def _default_period_type(self):
        selection = self.get_period_type_selection()
        return selection and selection[0][0] or False

    def _default_year(self):
        return fields.Date.from_string(fields.Date.today()).year

    def _default_number(self):
        return self._aeat_number

    def _get_export_config(self, date):
        model = self.env['ir.model'].search([('model', '=', self._name)])
        return self.env['aeat.model.export.config'].search([
            ('model_id', '=', model.id),
            ('date_start', '<=', date),
            '|',
            ('date_end', '=', False),
            ('date_end', '>=', date),
        ], limit=1)

    def _default_export_config_id(self):
        return self._get_export_config(fields.Date.today())

    company_id = fields.Many2one(
        comodel_name='res.company', string="Company", required=True,
        readonly=True, default=_default_company_id,
        states={'draft': [('readonly', False)]})
    company_vat = fields.Char(
        string="VAT number", size=9, required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    number = fields.Char(
        string="Model number", size=3, required=True, readonly=True,
        default=_default_number)
    previous_number = fields.Char(
        string="Previous declaration number", size=13,
        states={'done': [('readonly', True)]})
    contact_name = fields.Char(
        string="Full Name", size=40, help="Must have name and surname.",
        required=True, readonly=True, states={'draft': [('readonly', False)]})
    contact_phone = fields.Char(
        string="Phone", size=9, required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    representative_vat = fields.Char(
        string="L.R. VAT number", size=9, readonly=True,
        help="Legal Representative VAT number.",
        states={'draft': [('readonly', False)]})
    year = fields.Integer(
        string="Year", default=_default_year, required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    type = fields.Selection(
        selection=[
            ('N', 'Normal'),
            ('C', 'Complementary'),
            ('S', 'Substitutive'),
        ], string="Statement Type", default='N', readonly=True, required=True,
        states={'draft': [('readonly', False)]})
    support_type = fields.Selection(
        selection=[
            ('C', 'DVD'),
            ('T', 'Telematics'),
        ], string="Support Type", default='T', readonly=True, required=True,
        states={'draft': [('readonly', False)]})
    calculation_date = fields.Datetime(string="Calculation date")
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('calculated', 'Processed'),
            ('done', 'Done'),
            ('posted', 'Posted'),
            ('cancelled', 'Cancelled'),
        ], string='State', default='draft', readonly=True)
    name = fields.Char(string="Report identifier", size=13, oldname='sequence')
    model_id = fields.Many2one(
        comodel_name="ir.model", string="Model",
        compute='_compute_report_model', oldname='model')
    export_config_id = fields.Many2one(
        comodel_name='aeat.model.export.config', string="Export config",
        domain=lambda self: [
            ('model_id', '=',
             self.env['ir.model'].search([('model', '=', self._name)]).id)
        ],
        default=_default_export_config_id, oldname='export_config')
    currency_id = fields.Many2one(
        comodel_name='res.currency', string="Currency", readonly=True,
        related='company_id.currency_id')
    period_type = fields.Selection(
        selection='get_period_type_selection', string="Period type",
        required=True, default=_default_period_type,
        readonly=True, states={'draft': [('readonly', False)]})
    date_start = fields.Date(
        string="Starting date", required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    date_end = fields.Date(
        string="Ending date", required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    allow_posting = fields.Boolean(compute="_compute_allow_posting")
    counterpart_account_id = fields.Many2one(
        comodel_name='account.account', string="Counterpart account",
        help="This account will be the counterpart for all the journal items "
             "that are regularized when posting the report.",
        oldname='counterpart_account')
    journal_id = fields.Many2one(
        comodel_name='account.journal', string="Journal",
        domain=[('type', '=', 'general')], default=_default_journal,
        help="Journal in which post the move.",
        states={'done': [('readonly', True)]})
    move_id = fields.Many2one(
        comodel_name='account.move', string="Account entry", readonly=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner', string="Partner",
        related='company_id.partner_id', readonly=True)
    partner_bank_id = fields.Many2one(
        comodel_name='res.partner.bank', string='Bank account',
        help='Company bank account used for the presentation',
        domain="[('acc_type', '=', 'iban'), "
               " ('partner_id', '=', partner_id)]")
    exception_msg = fields.Char('Exception message',
                                compute='_compute_exception_msg')

    @api.multi
    def _compute_exception_msg(self):
        """To override"""

    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)',
         'AEAT report identifier must be unique'),
    ]

    @api.multi
    def _compute_report_model(self):
        for report in self:
            report.model_id = self.env['ir.model'].search([
                ('model', '=', report._name),
            ]).id

    @api.multi
    def _compute_allow_posting(self):
        for report in self:
            report.allow_posting = False

    @api.multi
    @api.constrains('type', 'previous_number')
    def _check_previous_number(self):
        for report in self:
            if report.type in ('C', 'S') and not report.previous_number:
                raise exceptions.UserError(
                    _("If this declaration is complementary or substitutive, "
                      "a previous declaration number should be provided.")
                )

    @api.onchange('company_id')
    def onchange_company_id(self):
        """Load some company data (the VAT number) when company changes.
        """
        if self.company_id.vat:
            # Remove the ES part from spanish vat numbers
            #  (ES12345678Z => 12345678Z)
            self.company_vat = re.match(
                "(ES){0,1}(.*)", self.company_id.vat).groups()[1]
        self.contact_name = self.env.user.name
        self.contact_phone = self._filter_phone(
            self.env.user.partner_id.phone or
            self.env.user.partner_id.mobile or
            self.env.user.company_id.phone)

    @api.onchange('year', 'period_type')
    def onchange_period_type(self):
        if not self.year or not self.period_type:
            self.date_start = False
            self.date_end = False
        else:
            if self.period_type == '0A':
                # Anual
                self.date_start = fields.Date.from_string(
                    '%s-01-01' % self.year)
                self.date_end = fields.Date.from_string(
                    '%s-12-31' % self.year)
            elif self.period_type in ('1T', '2T', '3T', '4T'):
                # Trimestral
                starting_month = 1 + (int(self.period_type[0]) - 1) * 3
                ending_month = starting_month + 2
                self.date_start = fields.Date.from_string(
                    '%s-%s-01' % (self.year, starting_month))
                self.date_end = fields.Date.from_string(
                    '%s-%s-%s' % (
                        self.year, ending_month,
                        monthrange(self.year, ending_month)[1]))
            elif self.period_type in ('01', '02', '03', '04', '05', '06',
                                      '07', '08', '09', '10', '11', '12'):
                # Mensual
                month = int(self.period_type)
                self.date_start = fields.Date.from_string(
                    '%s-%s-01' % (self.year, month))
                self.date_end = fields.Date.from_string('%s-%s-%s' % (
                    self.year, month, monthrange(self.year, month)[1]))
            self.export_config_id = self._get_export_config(self.date_start).id

    @api.model
    def _report_identifier_get(self, vals):
        seq_name = "aeat%s-sequence" % self._aeat_number
        company_id = vals.get('company_id', self.env.user.company_id.id)
        seq = self.env['ir.sequence'].search(
            [('name', '=', seq_name), ('company_id', '=', company_id)],
            limit=1,
        )
        if not seq:
            raise exceptions.UserError(_(
                "AEAT model sequence not found. You can try to restart your "
                "Odoo service for recreating the sequences."
            ))
        return seq.next_by_id()

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self._report_identifier_get(vals)
        return super(L10nEsAeatReport, self).create(vals)

    @api.multi
    def button_calculate(self):
        res = self.calculate()
        self.write({'state': 'calculated',
                    'calculation_date': fields.Datetime.now()})
        return res

    @api.multi
    def button_recalculate(self):
        self.write({'calculation_date': fields.Datetime.now()})
        return self.calculate()

    @api.multi
    def _get_previous_fiscalyear_reports(self, date):
        """Get the AEAT reports previous to the given date.

        :param date: Date for looking for previous reports.
        :return: Recordset of the previous AEAT reports. None if there is no
                 previous reports.
        """
        self.ensure_one()
        return self.search([
            ('year', '=', self.year),
            ('date_start', '<', date),
        ])

    @api.multi
    def calculate(self):
        """To be overrided by inherit models"""
        return True

    @api.multi
    def button_confirm(self):
        """Set report status to done."""
        self.write({'state': 'done'})
        return True

    @api.multi
    def _prepare_move_vals(self):
        self.ensure_one()
        return {
            'date': self.date_end,
            'journal_id': self.journal_id.id,
            'ref': self.name,
            'company_id': self.company_id.id,
        }

    @api.multi
    def button_post(self):
        """Create any possible account move and set state to posted."""
        for report in self:
            report.create_regularization_move()
        self.write({'state': 'posted'})
        return True

    @api.multi
    def button_cancel(self):
        """Set report status to cancelled."""
        self.write({'state': 'cancelled'})
        return True

    @api.multi
    def button_unpost(self):
        """Remove created account move and set state to cancelled."""
        self.mapped('move_id').unlink()
        self.write({'state': 'cancelled'})
        return True

    @api.multi
    def button_recover(self):
        """Set report status to draft and reset calculation date."""
        self.write({'state': 'draft', 'calculation_date': False})
        return True

    @api.multi
    def button_export(self):
        for report in self:
            export_obj = self.env[
                "l10n.es.aeat.report.%s.export_to_boe" % report.number]
            export_obj.export_boe_file(report)
        return True

    @api.multi
    def button_open_move(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_line_form').read()[0]
        action['view_mode'] = 'form'
        action['res_id'] = self.move_id.id
        del action['view_id']
        del action['views']
        return action

    @api.multi
    def unlink(self):
        if any(item.state not in ['draft', 'cancelled'] for item in self):
            raise exceptions.UserError(_("Only reports in 'draft' or "
                                       "'cancelled' state can be removed"))
        return super(L10nEsAeatReport, self).unlink()

    @api.model
    def _prepare_aeat_sequence_vals(self, sequence, aeat_num, company):
        return {
            'name': sequence,
            'code': 'aeat.sequence.type',
            'number_increment': 1,
            'implementation': 'no_gap',
            'padding': 13 - len(str(aeat_num)),
            'number_next_actual': 1,
            'prefix': aeat_num,
            'company_id': company.id,
        }

    @api.model
    def _filter_phone(self, phone):
        return (phone or '').replace(" ", "")[-9:]

    @api.model_cr
    def _register_hook(self):
        res = super(L10nEsAeatReport, self)._register_hook()
        if self._name in ('l10n.es.aeat.report',
                          'l10n.es.aeat.report.tax.mapping'):
            return res
        aeat_num = getattr(self, '_aeat_number', False)
        if not aeat_num:
            raise exceptions.UserError(_(
                "Modelo no válido: %s. Debe declarar una variable "
                "'_aeat_number'" % self._name
            ))
        seq_obj = self.env['ir.sequence']
        sequence = "aeat%s-sequence" % aeat_num
        companies = self.env['res.company'].search([])
        for company in companies:
            seq = seq_obj.search([
                ('name', '=', sequence), ('company_id', '=', company.id),
            ])
            if seq:
                continue
            seq_obj.create(self.env[self._name]._prepare_aeat_sequence_vals(
                sequence, aeat_num, company,
            ))
        return res

    @api.model
    def _get_formatted_date(self, date):
        """Convert an Odoo date to BOE export date format.

        :param date: Date in Odoo format or falsy value
        :return: Date formatted for BOE export.
        """
        if not date:
            return ''
        return datetime.strftime(fields.Date.from_string(date), "%d%m%Y")

    @api.model
    def get_html(self, given_context=None):
        """ Render dynamic view from ir.action.client"""
        result = {}
        rcontext = {}
        rec = self.browse(given_context.get('active_id'))
        if rec:
            rcontext['o'] = rec
            result['html'] = self.env.ref(given_context.get(
                'template_name')).render(
                rcontext)
        return result
