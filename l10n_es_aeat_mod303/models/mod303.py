# -*- coding: utf-8 -*-
# © 2013 - Guadaltech - Alberto Martín Cortada
# © 2015 - AvanzOSC - Ainara Galdona
# © 2014-2016 - Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod303.report"
    _description = "AEAT 303 Report"

    def _get_export_conf(self):
        try:
            return self.env.ref(
                'l10n_es_aeat_mod303.aeat_mod303_main_export_config').id
        except ValueError:
            return self.env['aeat.model.export.config']

    def _default_counterpart_303(self):
        return self.env['account.account'].search(
            [('code', 'like', '4750%'), ('type', '!=', 'view')])[:1]

    @api.multi
    @api.depends('tax_lines', 'tax_lines.amount')
    def _compute_total_devengado(self):
        casillas_devengado = (3, 6, 9, 11, 13, 15, 18, 21, 24, 26)
        for report in self:
            tax_lines = report.tax_lines.filtered(
                lambda x: x.field_number in casillas_devengado)
            report.total_devengado = sum(tax_lines.mapped('amount'))

    @api.multi
    @api.depends('tax_lines', 'tax_lines.amount')
    def _compute_total_deducir(self):
        casillas_deducir = (29, 31, 33, 35, 37, 39, 41, 42, 43, 44)
        for report in self:
            tax_lines = report.tax_lines.filtered(
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
                report.casilla_46 * report.porcentaje_atribuible_estado / 100)

    @api.multi
    @api.depends('atribuible_estado', 'cuota_compensar',
                 'regularizacion_anual')
    def _compute_casilla_69(self):
        for report in self:
            report.casilla_69 = (
                report.atribuible_estado + report.cuota_compensar +
                report.regularizacion_anual)

    @api.multi
    @api.depends('casilla_69', 'previous_result')
    def _compute_resultado_liquidacion(self):
        for report in self:
            report.resultado_liquidacion = (
                report.casilla_69 - report.previous_result)

    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Currency',
        related='company_id.currency_id', store=True, readonly=True)
    number = fields.Char(default='303')
    export_config = fields.Many2one(default=_get_export_conf)
    company_partner_id = fields.Many2one('res.partner', string='Partner',
                                         relation='company_id.partner_id',
                                         store=True)
    devolucion_mensual = fields.Boolean(
        string="Devolución mensual", states={'done': [('readonly', True)]},
        help="Inscrito en el Registro de Devolución Mensual")
    total_devengado = fields.Float(
        string="[27] IVA devengado", readonly=True,
        compute="_compute_total_devengado", store=True)
    total_deducir = fields.Float(
        string="[45] IVA a deducir", readonly=True,
        compute="_compute_total_deducir", store=True)
    casilla_46 = fields.Float(
        string="[46] Resultado régimen general", readonly=True, store=True,
        help="(IVA devengado - IVA deducible)", compute="_compute_casilla_46")
    porcentaje_atribuible_estado = fields.Float(
        string="[65] % atribuible al Estado",
        states={'done': [('readonly', True)]},
        help="Los sujetos pasivos que tributen conjuntamente a la "
             "Administración del Estado y a las Diputaciones Forales del País "
             "Vasco o a la Comunidad Foral de Navarra, consignarán en esta "
             "casilla el porcentaje del volumen de operaciones en territorio "
             "común. Los demás sujetos pasivos consignarán en esta casilla el "
             "100%", default=100)
    atribuible_estado = fields.Float(
        string="[66] Atribuible a la Administración", readonly=True,
        compute="_compute_atribuible_estado", store=True)
    cuota_compensar = fields.Float(
        string="[67] Cuotas a compensar", default=0,
        states={'done': [('readonly', True)]},
        help="Cuota a compensar de periodos anteriores, en los que su "
             "declaración fue a devolver y se escogió la opción de "
             "compensación posterior")
    regularizacion_anual = fields.Float(
        string="[68] Regularización anual",
        states={'done': [('readonly', True)]},
        help="En la última autoliquidación del año (la del período 4T o mes "
             "12) se hará constar, con el signo que corresponda, el resultado "
             "de la regularización anual conforme disponen las Leyes por las "
             "que se aprueban el Concierto Económico entre el Estado y la "
             "Comunidad Autónoma del País Vasco y el Convenio Económico entre "
             "el Estado y la Comunidad Foral de Navarra.""")
    casilla_69 = fields.Float(
        string="[69] Resultado", readonly=True, compute="_compute_casilla_69",
        help="Atribuible a la Administración [66] - Cuotas a compensar [67] + "
             "Regularización anual [68]""", store=True)
    previous_result = fields.Float(
        string="[70] A deducir",
        help="Resultado de la anterior o anteriores declaraciones del mismo "
             "concepto, ejercicio y periodo",
        states={'done': [('readonly', True)]})
    resultado_liquidacion = fields.Float(
        string="[71] Result. liquidación", readonly=True,
        compute="_compute_resultado_liquidacion", store=True)
    result_type = fields.Selection(
        selection=[('I', 'A ingresar'),
                   ('D', 'A devolver'),
                   ('N', 'Sin actividad/Resultado cero')],
        compute="_compute_result_type")
    compensate = fields.Boolean(
        string="Compensate", states={'done': [('readonly', True)]},
        help="Si se marca, indicará que el importe a devolver se compensará "
             "en posteriores declaraciones")
    bank_account = fields.Many2one(
        comodel_name="res.partner.bank", string="Bank account",
        states={'done': [('readonly', True)]})
    counterpart_account = fields.Many2one(default=_default_counterpart_303)
    allow_posting = fields.Boolean(default=True)

    def __init__(self, pool, cr):
        self._aeat_number = '303'
        super(L10nEsAeatMod303Report, self).__init__(pool, cr)

    @api.one
    def _compute_allow_posting(self):
        self.allow_posting = True

    @api.one
    @api.depends('resultado_liquidacion')
    def _compute_result_type(self):
        if self.resultado_liquidacion == 0:
            self.result_type = 'N'
        elif self.resultado_liquidacion > 0:
            self.result_type = 'I'
        else:
            self.result_type = 'D'

    @api.onchange('period_type', 'fiscalyear_id')
    def onchange_period_type(self):
        super(L10nEsAeatMod303Report, self).onchange_period_type()
        if self.period_type not in ('4T', '12'):
            self.regularizacion_anual = 0

    @api.onchange('type')
    def onchange_type(self):
        if self.type != 'C':
            self.previous_result = 0

    @api.onchange('result_type')
    def onchange_result_type(self):
        if self.result_type != 'B':
            self.compensate = False

    @api.multi
    def button_confirm(self):
        """Check records"""
        msg = ""
        for mod303 in self:
            if mod303.result_type == 'I' and not mod303.bank_account:
                msg = _('Select an account for making the charge')
            if mod303.result_type == 'B' and not not mod303.bank_account:
                msg = _('Select an account for receiving the money')
        if msg:
            # Don't raise error, because data is not used
            # raise exceptions.Warning(msg)
            pass
        return super(L10nEsAeatMod303Report, self).button_confirm()
