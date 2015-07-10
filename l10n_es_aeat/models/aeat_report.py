# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es)
#        Luis Manuel Angueira Blanco (Pexego)
#    Copyright (C) 2013
#        Ignacio Ibeas - Acysos S.L. (http://acysos.com)
#        Migración a OpenERP 7.0
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import fields, models, api, exceptions, _
from openerp import SUPERUSER_ID
from datetime import datetime
import re


class L10nEsAeatReport(models.AbstractModel):
    _name = "l10n.es.aeat.report"
    _description = "AEAT report base module"
    _rec_name = 'sequence'
    _aeat_number = False
    _period_quarterly = True
    _period_monthly = True
    _period_yearly = False

    def _default_company(self):
        company_obj = self.env['res.company']
        return company_obj._company_default_get('l10n.es.aeat.report')

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
        [('draft', 'Draft'), ('calculated', 'Processed'), ('done', 'Done'),
         ('cancelled', 'Cancelled')], string='State', readonly=True,
        default='draft')
    sequence = fields.Char(string="Sequence", size=16)
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
    tax_lines = fields.One2many(
        comodel_name='l10n.es.aeat.tax.line', inverse_name='report',
        readonly=True)

    _sql_constraints = [
        ('sequence_uniq', 'unique(sequence)',
         'AEAT report sequence must be unique'),
    ]

    @api.one
    def _compute_report_model(self):
        self.model = self.env['ir.model'].search([('model', '=', self._name)])

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

    @api.model
    def create(self, values):
        seq_obj = self.env['ir.sequence']
        sequence = "aeat%s-sequence" % self._model._aeat_number
        seq = seq_obj.next_by_id(seq_obj.search([('name', '=', sequence)]).id)
        values['sequence'] = seq
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
    def calculate(self):
        for report in self:
            if not report.periods:
                raise exceptions.Warning(
                    'There is no period defined for the report. Please set '
                    'at least one period and try again.')
            report.tax_lines.unlink()
            # Buscar configuración de mapeo de impuestos
            tax_code_map_obj = self.env['aeat.mod.map.tax.code']
            date_start = min([fields.Date.from_string(x) for x in
                              self.periods.mapped('date_start')])
            date_stop = max([fields.Date.from_string(x) for x in
                             self.periods.mapped('date_stop')])
            tax_code_map = tax_code_map_obj.search(
                [('model', '=', report.number),
                 '|',
                 ('date_from', '<=', date_start),
                 ('date_from', '=', False),
                 '|',
                 ('date_to', '>=', date_stop),
                 ('date_to', '=', False)], limit=1)
            if tax_code_map:
                tax_lines = []
                for line in tax_code_map.map_lines:
                    move_lines = self.env['account.move.line']
                    for tax_code in line.tax_codes:
                        move_lines += report._get_tax_code_lines(
                            tax_code, periods=report.periods)
                    tax_lines.append({
                        'map_line': line.id,
                        'amount': sum([x.tax_amount for x in move_lines]),
                        'move_lines': [(6, 0, move_lines.ids)],
                    })
                report.tax_lines = [(0, 0, x) for x in tax_lines]
        return True

    @api.multi
    def button_confirm(self):
        """Set report status to done."""
        self.write({'state': 'done'})
        return True

    @api.multi
    def button_cancel(self):
        """Set report status to cancelled."""
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
    def unlink(self):
        if any(item.state not in ['draft', 'cancelled'] for item in self):
            raise exceptions.Warning(_("Only reports in 'draft' or "
                                       "'cancelled' state can be removed"))
        return super(L10nEsAeatReport, self).unlink()

    def init(self, cr):
        if self._name != 'l10n.es.aeat.report':
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
                                'padding': 9,
                                'number_next_actual': 1,
                                'prefix': aeat_num + '-'
                                }
                    seq_obj.create(cr, SUPERUSER_ID, seq_vals)
            except:
                raise exceptions.Warning(
                    "Modelo no válido: %s. Debe declarar una variable "
                    "'_aeat_number'" % self._name)

    # Helper functions
    @api.multi
    def _get_partner_domain(self):
        return []

    @api.multi
    def _get_move_line_domain(self, tax_code_template, periods=None,
                              include_children=True):
        self.ensure_one()
        tax_code_model = self.env['account.tax.code']
        tax_code = tax_code_model.search(
            [('code', '=', tax_code_template.code),
             ('company_id', '=', self.company_id.id)], limit=1)
        if include_children and tax_code:
            tax_codes = tax_code_model.search(
                [('id', 'child_of', tax_code.id),
                 ('company_id', '=', self.company_id.id)])
        else:
            tax_codes = tax_code
        if not periods:
            periods = self.env['account.period'].search(
                [('fiscalyear_id', '=', self.fiscalyear_id.id)])
        move_line_domain = [('company_id', '=', self.company_id.id),
                            ('tax_code_id', 'child_of', tax_codes.ids),
                            ('period_id', 'in', periods.ids)]
        move_line_domain += self._get_partner_domain()
        return move_line_domain

    @api.multi
    def _get_tax_code_lines(self, tax_code_template, periods=None,
                            include_children=True):
        self.ensure_one()
        domain = self._get_move_line_domain(
            tax_code_template, periods=periods,
            include_children=include_children)
        return self.env['account.move.line'].search(domain)


class L10nEsAeatTaxLine(models.Model):
    _name = "l10n.es.aeat.tax.line"

    report = fields.Many2one('l10n.es.aeat.report', required=True)
    field_number = fields.Integer(
        string="Field number", related="map_line.field_number",
        store=True)
    name = fields.Char(
        string="Name", related="map_line.name", store=True)
    amount = fields.Float()
    map_line = fields.Many2one(
        comodel_name='aeat.mod.map.tax.code.line', required=True)
    move_lines = fields.Many2many(
        comodel_name='account.move.line', string='Journal items')

    def _get_move_line_act_window_dict(self):
        return self.env.ref('account.action_tax_code_line_open').read()[0]

    @api.multi
    def get_calculated_move_lines(self):
        res = self._get_move_line_act_window_dict()
        res['domain'] = [('id', 'in', self.move_lines.ids)]
        return res
