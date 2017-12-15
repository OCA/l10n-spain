# -*- coding: utf-8 -*-
# © 2013 - Guadaltech - Alberto Martín Cortada
# © 2015 - AvanzOSC - Ainara Galdona
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2014-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, exceptions, fields, models, _


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod303.report"
    _description = "AEAT 303 Report"
    _aeat_number = '303'

    def _default_counterpart_303(self):
        return self.env['account.account'].search([
            ('code', 'like', '4750%'),
        ])[:1]

    company_partner_id = fields.Many2one(
        comodel_name='res.partner', string="Partner",
        relation='company_id.partner_id', store=True)
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
    bank_account_id = fields.Many2one(
        comodel_name="res.partner.bank", string="Bank account",
        states={'done': [('readonly', True)]}, oldname='bank_account')
    counterpart_account_id = fields.Many2one(
        comodel_name='account.account', string="Counterpart account",
        default=_default_counterpart_303, oldname='counterpart_account')
    allow_posting = fields.Boolean(string="Allow posting", default=True)

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
    def button_confirm(self):
        """Check records"""
        msg = ""
        for mod303 in self:
            if mod303.result_type == 'I' and not mod303.bank_account_id:
                msg = _('Select an account for making the charge')
            if mod303.result_type == 'D' and not mod303.bank_account_id:
                msg = _('Select an account for receiving the money')
        if msg:
            # Don't raise error, because data is not used
            # raise exceptions.Warning(msg)
            pass
        return super(L10nEsAeatMod303Report, self).button_confirm()

    @api.multi
    @api.constrains('cuota_compensar')
    def check_qty(self):
        for record in self:
            if record.cuota_compensar < 0.0:
                raise exceptions.ValidationError(
                    _('The fee to compensate must be indicated '
                      'as a positive number. '))
