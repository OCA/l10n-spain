# -*- coding: utf-8 -*-
# © 2004-2011 - Pexego Sistemas Informáticos - Luis Manuel Angueira Blanco
# © 2013 - Acysos S.L. - Ignacio Ibeas (Migración a v7)
# © 2014-2016 - Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models, api, exceptions, SUPERUSER_ID, _
from datetime import datetime
import re


class L10nEsAeatReport(models.AbstractModel):
    _name = "l10n.es.aeat.report"
    _description = "AEAT report base module"
    _rec_name = 'name'
    _aeat_number = False
    _period_quarterly = True
    _period_monthly = True
    _period_yearly = False

    def _default_company(self):
        company_obj = self.env['res.company']
        return company_obj._company_default_get('l10n.es.aeat.report')

    def _default_journal(self):
        return self.env['account.journal'].search(
            [('type', '=', 'general')])[:1]

    def get_period_type_selection(self):
        period_types = []
        if self._period_yearly:
            period_types += [('0A', '0A - Anual')]
        if self._period_quarterly:
            period_types += [('1T', '1T - Primer trimestre'),
                             ('2T', '2T - Segundo trimestre'),
                             ('3T', '3T - Tercer trimestre'),
                             ('4T', '4T - Cuarto trimestre')]
        if self._period_monthly:
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

    company_id = fields.Many2one(
        'res.company', string='Company', required=True, readonly=True,
        default=_default_company, states={'draft': [('readonly', False)]})
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
        states={'calculated': [('required', True)],
                'confirmed': [('readonly', True)]})
    contact_phone = fields.Char(
        string="Phone", size=9, states={'calculated': [('required', True)],
                                        'confirmed': [('readonly', True)]})
    representative_vat = fields.Char(
        string='L.R. VAT number', size=9,
        help="Legal Representative VAT number.",
        states={'confirmed': [('readonly', True)]})
    fiscalyear_id = fields.Many2one(
        'account.fiscalyear', string='Fiscal year', required=True,
        readonly=True, states={'draft': [('readonly', False)]})
    type = fields.Selection(
        [('N', 'Normal'), ('C', 'Complementary'), ('S', 'Substitutive')],
        string='Statement Type', default='N', readonly=True, required=True,
        states={'draft': [('readonly', False)]})
    support_type = fields.Selection(
        [('C', 'DVD'), ('T', 'Telematics')], string='Support Type',
        default='T', states={'calculated': [('required', True)],
                             'done': [('readonly', True)]})
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
    periods = fields.Many2many(
        comodel_name='account.period', readonly=True, string="Period(s)",
        states={'draft': [('readonly', False)]})
    allow_posting = fields.Boolean(compute="_compute_allow_posting")
    counterpart_account = fields.Many2one(
        comodel_name="account.account",
        help="This account will be the counterpart for all the journal items "
             "that are regularized when posting the report.")
    journal_id = fields.Many2one(
        comodel_name="account.journal", string="Journal",
        domain=[('type', '=', 'general')], default=_default_journal,
        help="Journal in which post the move.")
    move_id = fields.Many2one(
        comodel_name="account.move", string="Account entry")

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
    def on_change_company_id(self):
        """Loads some company data (the VAT number) when the selected
        company changes.
        """
        if self.company_id.vat:
            # Remove the ES part from spanish vat numbers
            #  (ES12345678Z => 12345678Z)
            self.company_vat = re.match(
                "(ES){0,1}(.*)", self.company_id.vat).groups()[1]
        self.contact_name = self.env.user.name
        self.contact_phone = self.env.user.partner_id.phone

    @api.onchange('period_type', 'fiscalyear_id')
    def onchange_period_type(self):
        period_model = self.env['account.period']
        if not self.fiscalyear_id:
            self.periods = False
        else:
            fy_date_start = fields.Date.from_string(
                self.fiscalyear_id.date_start)
            fy_date_stop = fields.Date.from_string(
                self.fiscalyear_id.date_stop)
            if self.period_type == '0A':
                # Anual
                if fy_date_start.year != fy_date_stop.year:
                    return {
                        'warning': _(
                            'Split fiscal years cannot be automatically '
                            'handled. You should select manually the periods.')
                    }
                self.periods = self.fiscalyear_id.period_ids.filtered(
                    lambda x: not x.special)
            elif self.period_type in ('1T', '2T', '3T', '4T'):
                # Trimestral
                start_month = (int(self.period_type[:1]) - 1) * 3 + 1
                # Para manejar ejercicios fiscales divididos en dos periodos
                year = (fy_date_start.year if
                        start_month < fy_date_start.month else
                        fy_date_stop.year)
                period = period_model.find(
                    dt=fields.Date.to_string(
                        datetime(year=year, month=start_month, day=1)))
                period_date_stop = fields.Date.from_string(period.date_stop)
                self.periods = period
                if period_date_stop.month != start_month + 2:
                    # Los periodos no están definidos trimestralmente
                    for i in range(1, 3):
                        month = start_month + i
                        period = period_model.find(
                            dt=fields.Date.to_string(
                                datetime(year=year, month=month, day=1)))
                        self.periods += period
            elif self.period_type in ('01', '02', '03', '04', '05', '06',
                                      '07', '08', '09', '10', '11', '12'):
                # Mensual
                month = int(self.period_type)
                # Para manejar ejercicios fiscales divididos en dos periodos
                year = (fy_date_start.year if month < fy_date_start.month else
                        fy_date_stop.year)
                period = period_model.find(
                    dt=fields.Date.to_string(
                        datetime(year=year, month=month, day=1)))
                period_date_start = fields.Date.from_string(period.date_start)
                period_date_stop = fields.Date.from_string(period.date_stop)
                if period_date_start.month != period_date_stop.month:
                    return {
                        'warning': _(
                            'It seems that you have defined quarterly periods '
                            'or periods in the middle of the month. This '
                            'cannot be automatically handled. You should '
                            'select manually the periods.')
                    }
                self.periods = period

    def _name_get(self):
        seq_obj = self.env['ir.sequence']
        sequence = "aeat%s-sequence" % self._model._aeat_number
        return seq_obj.next_by_id(seq_obj.search([('name', '=', sequence)]).id)

    @api.model
    def create(self, values):
        values['name'] = self._name_get()
        return super(L10nEsAeatReport, self).create(values)

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
        return {
            'date': fields.Date.today(),
            'journal_id': self.journal_id.id,
            'period_id': self.env['account.period'].find().id,
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

    def init(self, cr):
        # TODO: Poner en el _register_hook para evitar choque en multi BDs
        if self._name not in ('l10n.es.aeat.report',
                              'l10n.es.aeat.report.tax.mapping'):
            seq_obj = self.pool['ir.sequence']
            try:
                aeat_num = getattr(self, '_aeat_number')
                if not aeat_num:
                    raise Exception()
                sequence = "aeat%s-sequence" % aeat_num
                if not seq_obj.search(cr, SUPERUSER_ID,
                                      [('name', '=', sequence)]):
                    seq_vals = {'name': sequence,
                                'code': 'aeat.sequence.type',
                                'number_increment': 1,
                                'implementation': 'no_gap',
                                'padding': 13 - len(str(aeat_num)),
                                'number_next_actual': 1,
                                'prefix': aeat_num
                                }
                    seq_obj.create(cr, SUPERUSER_ID, seq_vals)
            except:
                raise exceptions.Warning(
                    "Modelo no válido: %s. Debe declarar una variable "
                    "'_aeat_number'" % self._name)
