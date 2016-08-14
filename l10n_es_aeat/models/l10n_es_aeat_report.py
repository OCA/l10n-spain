# -*- coding: utf-8 -*-
# © 2004-2011 - Pexego Sistemas Informáticos - Luis Manuel Angueira Blanco
# © 2013 - Acysos S.L. - Ignacio Ibeas (Migración a v7)
# © 2014-2016 - Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models, api, exceptions, SUPERUSER_ID, _
from calendar import monthrange
from openerp.tools import config
import re


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

    company_id = fields.Many2one(
        'res.company', string='Company', required=True, readonly=True,
        default=_default_company_id, states={'draft': [('readonly', False)]})
    company_vat = fields.Char(
        string='VAT number', size=9, required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    number = fields.Char(
        string='Declaration number', size=13, required=True, readonly=True)
    previous_number = fields.Char(
        string='Previous declaration number', size=13,
        states={'done': [('readonly', True)]})
    contact_name = fields.Char(
        string="Full Name", size=40, help="Must have name and surname.",
        required=True, readonly=True, states={'draft': [('readonly', False)]})
    contact_phone = fields.Char(
        string="Phone", size=9, required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    representative_vat = fields.Char(
        string='L.R. VAT number', size=9, readonly=True,
        help="Legal Representative VAT number.",
        states={'draft': [('readonly', False)]})
    year = fields.Integer(
        string="Year", default=_default_year, required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    type = fields.Selection(
        [('N', 'Normal'), ('C', 'Complementary'), ('S', 'Substitutive')],
        string='Statement Type', default='N', readonly=True, required=True,
        states={'draft': [('readonly', False)]})
    support_type = fields.Selection(
        [('C', 'DVD'), ('T', 'Telematics')], string='Support Type',
        readonly=True, required=True, default='T',
        states={'draft': [('readonly', False)]})
    calculation_date = fields.Datetime(string="Calculation date")
    state = fields.Selection(
        [('draft', 'Draft'),
         ('calculated', 'Processed'),
         ('done', 'Done'),
         ('posted', 'Posted'),
         ('cancelled', 'Cancelled')], string='State', readonly=True,
        default='draft')
    name = fields.Char(string="Report identifier", size=13, oldname='sequence')
    model = fields.Many2one(
        comodel_name="ir.model", compute='_compute_report_model')
    export_config = fields.Many2one(
        comodel_name='aeat.model.export.config', string='Export config',
        domain="[('model', '=', model)]")
    period_type = fields.Selection(
        selection="get_period_type_selection", string="Period type",
        required=True, default=_default_period_type,
        readonly=True, states={'draft': [('readonly', False)]})
    date_start = fields.Date(
        string="Starting date", required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    date_end = fields.Date(
        string="Ending date", required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    allow_posting = fields.Boolean(compute="_compute_allow_posting")
    counterpart_account = fields.Many2one(
        comodel_name="account.account",
        help="This account will be the counterpart for all the journal items "
             "that are regularized when posting the report.")
    journal_id = fields.Many2one(
        comodel_name="account.journal", string="Journal",
        domain=[('type', '=', 'general')], default=_default_journal,
        help="Journal in which post the move.",
        states={'done': [('readonly', True)]})
    move_id = fields.Many2one(
        comodel_name="account.move", string="Account entry", readonly=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         'AEAT report identifier must be unique'),
    ]

    @api.one
    def _compute_report_model(self):
        self.model = self.env['ir.model'].search([('model', '=', self._name)])

    @api.one
    def _compute_allow_posting(self):
        self.allow_posting = False

    @api.onchange('company_id')
    def onchange_company_id(self):
        """Loads some company data (the VAT number) when the selected
        company changes.
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

    @api.model
    def _report_identifier_get(self, vals):
        seq_name = "aeat%s-sequence" % self._model._aeat_number
        company_id = vals.get('company_id', self.env.user.company_id.id)
        seq = self.env['ir.sequence'].search(
            [('name', '=', seq_name), ('company_id', '=', company_id)],
            limit=1)
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
        prev_periods = self.fiscalyear_id.period_ids.filtered(
            lambda x: not x.special and x.date_start < date)
        prev_reports = None
        for period in prev_periods:
            reports = self.search([('periods', '=', period.id)])
            if not reports:
                raise exceptions.Warning(
                    _("There's a missing previous declaration for the period "
                      "%s.") % period.name)
            if not prev_reports:
                prev_reports = reports
            else:
                prev_reports |= reports
        return prev_reports

    @api.multi
    def calculate(self):
        for report in self:
            if not report.periods:
                raise exceptions.Warning(
                    _('There is no period defined for the report. Please set '
                      'at least one period and try again.'))
        return True

    @api.multi
    def button_confirm(self):
        """Set report status to done."""
        self.write({'state': 'done'})
        return True

    @api.multi
    def _prepare_move_vals(self):
        self.ensure_one()
        last = self.periods.sorted(lambda x: x.date_stop)[-1:]
        return {
            'journal_id': self.journal_id.id,
            'date': last.date_stop,
            'period_id': last.id,
            'ref': self.name,
            'company_id': self.company_id.id,
        }

    @api.multi
    def button_post(self):
        """Create any possible account move and set state to posted."""
        self.create_regularization_move()
        self.write({'state': 'posted'})
        return True

    @api.multi
    def button_cancel(self):
        """Set report status to cancelled."""
        self.write({'state': 'cancelled'})
        return True

    @api.multi
    def button_unpost(self):
        """Remove created account move and set state to done."""
        self.mapped('move_id').unlink()
        self.write({'state': 'cancelled'})
        return True

    @api.multi
    def button_recover(self):
        """Set report status to draft and reset calculation date."""
        self.write({'state': 'draft', 'calculation_date': None})
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
            raise exceptions.Warning(_("Only reports in 'draft' or "
                                       "'cancelled' state can be removed"))
        return super(L10nEsAeatReport, self).unlink()

    @api.model
    def _prepare_aeat_sequence_vals(self, sequence, aeat_num):
        return {
            'name': sequence,
            'code': 'aeat.sequence.type',
            'number_increment': 1,
            'implementation': 'no_gap',
            'padding': 13 - len(str(aeat_num)),
            'number_next_actual': 1,
            'prefix': aeat_num
        }

    @api.model
    def _filter_phone(self, phone):
        return (phone or '').replace(" ", "")[-9:]

    @api.cr
    def _register_hook(self, cr):
        res = super(L10nEsAeatReport, self)._register_hook(cr)
        if self._name not in ('l10n.es.aeat.report',
                              'l10n.es.aeat.report.tax.mapping'):
            with api.Environment.manage():
                env = api.Environment(cr, SUPERUSER_ID, {})
                seq_obj = env['ir.sequence']
                aeat_obj = env[self._name]
                try:
                    aeat_num = getattr(self, '_aeat_number')
                    if not aeat_num:
                        raise Exception()
                    sequence = "aeat%s-sequence" % aeat_num
                    if not seq_obj.search([('name', '=', sequence)]):
                        seq_obj.create(aeat_obj._prepare_aeat_sequence_vals(
                            sequence, aeat_num))
                except:
                    raise exceptions.Warning(
                        "Modelo no válido: %s. Debe declarar una variable "
                        "'_aeat_number'" % self._name)
        return res
