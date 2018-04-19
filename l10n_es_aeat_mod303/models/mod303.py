# Copyright 2013 - Guadaltech - Alberto Martín Cortada
# Copyright 2015 - AvanzOSC - Ainara Galdona
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2014-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, exceptions, fields, models, _

_ACCOUNT_PATTERN_MAP = {
    'C': '4700',
    'D': '4700',
    'N': '4700',
    'I': '4750',
}


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod303.report"
    _description = "AEAT 303 Report"
    _aeat_number = '303'

    def _default_counterpart_303(self):
        return self.env['account.account'].search([
            ('code', 'like', '4750%'),
            ('company_id', '=', self._default_company_id().id)
        ])[:1]

    devolucion_mensual = fields.Boolean(
        string="Montly Return", states={'done': [('readonly', True)]},
        help="Registered in the Register of Monthly Return")
    total_devengado = fields.Float(
        string="[27] VAT payable", readonly=True, compute_sudo=True,
        compute='_compute_total_devengado', store=True)
    total_deducir = fields.Float(
        string="[45] VAT receivable", readonly=True, compute_sudo=True,
        compute='_compute_total_deducir', store=True)
    casilla_46 = fields.Float(
        string="[46] General scheme result", readonly=True, store=True,
        help="(VAT payable - VAT receivable)", compute='_compute_casilla_46')
    porcentaje_atribuible_estado = fields.Float(
        string="[65] % attributable to State", default=100,
        states={'done': [('readonly', True)]},
        help="Taxpayers who pay jointly to the Central Government and "
             "the Provincial Councils of the Basque Country or the "
             "Autonomous Community of Navarra, will enter in this box the "
             "percentage of volume operations in the common territory. "
             "Other taxpayers will enter in this box 100%")
    atribuible_estado = fields.Float(
        string="[66] Attributable to the Administration", readonly=True,
        compute='_compute_atribuible_estado', store=True)
    cuota_compensar = fields.Float(
        string="[67] Fees to compensate", default=0,
        states={'done': [('readonly', True)]},
        help="Fee to compensate for prior periods, in which his statement "
             "was to return and compensation back option was chosen")
    regularizacion_anual = fields.Float(
        string="[68] Annual regularization",
        states={'done': [('readonly', True)]},
        help="In the last auto settlement of the year, shall be recorded "
             "(the fourth period or 12th month), with the appropriate sign, "
             "the result of the annual adjustment as have the laws by the "
             "Economic Agreement approved between the State and the "
             "Autonomous Community the Basque Country and the "
             "Economic Agreement between the State and Navarre.")
    casilla_69 = fields.Float(
        string="[69] Result", readonly=True, compute='_compute_casilla_69',
        help="[66] Attributable to the Administration - "
             "[67] Fees to compensate + "
             "[68] Annual regularization", store=True)
    casilla_77 = fields.Float(
        string="[77] VAT deferred (Settle by customs)",
        help="Contributions of import tax included in the documents "
             "evidencing the payment made by the Administration and received "
             "in the settlement period. You can only complete this box "
             "when the requirements of Article 74.1 of the Tax Regulations "
             "Value Added are met.")
    previous_result = fields.Float(
        string="[70] To be deducted",
        help="Result of the previous or prior statements of the same concept, "
             "exercise and period",
        states={'done': [('readonly', True)]})
    resultado_liquidacion = fields.Float(
        string="[71] Settlement result", readonly=True,
        compute='_compute_resultado_liquidacion', store=True)
    result_type = fields.Selection(
        selection=[
            ('I', 'To enter'),
            ('D', 'To return'),
            ('C', 'To compensate'),
            ('N', 'No activity/Zero result'),
        ], string="Result type", compute='_compute_result_type')
    counterpart_account_id = fields.Many2one(
        comodel_name='account.account', string="Counterpart account",
        default=_default_counterpart_303,
        domain="[('company_id', '=', company_id)]",
        oldname='counterpart_account')
    allow_posting = fields.Boolean(string="Allow posting", default=True)

    @api.multi
    @api.depends('date_start', 'cuota_compensar')
    def _compute_exception_msg(self):
        super(L10nEsAeatMod303Report, self)._compute_exception_msg()
        for mod303 in self.filtered(lambda x: x.state != 'draft'):
            # Get result from previous declarations, in order to identify if
            # there is an amount to compensate.
            prev_reports = mod303._get_previous_fiscalyear_reports(
                mod303.date_start
            ).filtered(lambda x: x.state not in ['draft', 'cancelled'])
            if not prev_reports:
                continue
            prev_report = min(
                prev_reports, key=lambda x: abs(
                    fields.Date.from_string(x.date_end) -
                    fields.Date.from_string(mod303.date_start)
                ),
            )
            if prev_report.result_type == 'C' and not mod303.cuota_compensar:
                if mod303.exception_msg:
                    mod303.exception_msg += "\n"
                else:
                    mod303.exception_msg = ""
                mod303.exception_msg += _(
                    "In previous declarations this year you reported a "
                    "Result Type 'To Compensate'. You might need to fill "
                    "field '[67] Fees to compensate' in this declaration."
                )

    @api.multi
    @api.depends('tax_line_ids', 'tax_line_ids.amount')
    def _compute_total_devengado(self):
        casillas_devengado = (3, 6, 9, 11, 13, 15, 18, 21, 24, 26)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas_devengado)
            report.total_devengado = sum(tax_lines.mapped('amount'))

    @api.multi
    @api.depends('tax_line_ids', 'tax_line_ids.amount')
    def _compute_total_deducir(self):
        casillas_deducir = (29, 31, 33, 35, 37, 39, 41, 42, 43, 44)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas_deducir)
            report.total_deducir = sum(tax_lines.mapped('amount'))

    @api.multi
    @api.depends('total_devengado', 'total_deducir')
    def _compute_casilla_46(self):
        for report in self:
            report.casilla_46 = report.total_devengado - report.total_deducir

    @api.multi
    @api.depends('porcentaje_atribuible_estado', 'casilla_46')
    def _compute_atribuible_estado(self):
        for report in self:
            report.atribuible_estado = (
                report.casilla_46 * report.porcentaje_atribuible_estado / 100.)

    @api.multi
    @api.depends('atribuible_estado', 'cuota_compensar',
                 'regularizacion_anual', 'casilla_77')
    def _compute_casilla_69(self):
        for report in self:
            report.casilla_69 = (
                report.atribuible_estado + report.casilla_77 -
                report.cuota_compensar + report.regularizacion_anual)

    @api.multi
    @api.depends('casilla_69', 'previous_result')
    def _compute_resultado_liquidacion(self):
        for report in self:
            report.resultado_liquidacion = (
                report.casilla_69 - report.previous_result)

    @api.multi
    def _compute_allow_posting(self):
        for report in self:
            report.allow_posting = True

    @api.multi
    @api.depends(
        'resultado_liquidacion',
        'period_type',
        'devolucion_mensual',
    )
    def _compute_result_type(self):
        for report in self:
            if report.resultado_liquidacion == 0:
                report.result_type = 'N'
            elif report.resultado_liquidacion > 0:
                report.result_type = 'I'
            else:
                if (report.devolucion_mensual or
                        report.period_type in ('4T', '12')):
                    report.result_type = 'D'
                else:
                    report.result_type = 'C'

    @api.onchange('year', 'period_type')
    def onchange_period_type(self):
        super(L10nEsAeatMod303Report, self).onchange_period_type()
        if self.period_type not in ('4T', '12'):
            self.regularizacion_anual = 0

    @api.onchange('type')
    def onchange_type(self):
        if self.type != 'C':
            self.previous_result = 0

    @api.multi
    def calculate(self):
        res = super(L10nEsAeatMod303Report, self).calculate()
        for mod303 in self:
            mod303.counterpart_account_id = \
                self.env['account.account'].search([
                    ('code', '=like', '%s%%' % _ACCOUNT_PATTERN_MAP.get(
                        mod303.result_type, '4750')),
                    ('company_id', '=', mod303.company_id.id),
                ], limit=1)
            prev_reports = mod303._get_previous_fiscalyear_reports(
                mod303.date_start
            ).filtered(lambda x: x.state not in ['draft', 'cancelled'])
            if not prev_reports:
                continue
            prev_report = min(
                prev_reports, key=lambda x: abs(
                    fields.Date.from_string(x.date_end) -
                    fields.Date.from_string(mod303.date_start)
                ),
            )
            if prev_report.result_type == 'C':
                mod303.cuota_compensar = abs(prev_report.resultado_liquidacion)
        return res

    @api.multi
    def button_confirm(self):
        """Check records"""
        msg = ""
        for mod303 in self:
            if mod303.result_type == 'D' and not mod303.partner_bank_id:
                msg = _('Select an account for receiving the money')
        if msg:
            raise exceptions.Warning(msg)
        return super(L10nEsAeatMod303Report, self).button_confirm()

    @api.multi
    @api.constrains('cuota_compensar')
    def check_qty(self):
        if self.filtered(lambda x: x.cuota_compensar < 0.0):
            raise exceptions.ValidationError(_(
                'The fee to compensate must be indicated as a positive number.'
            ))
