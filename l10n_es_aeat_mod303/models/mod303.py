# -*- coding: utf-8 -*-
# Copyright 2013 - Guadaltech - Alberto Martín Cortada
# Copyright 2015 - AvanzOSC - Ainara Galdona
# Copyright 2014-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _

NON_EDITABLE_ON_DONE = {'done': [('readonly', True)]}


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod303.report"
    _description = "AEAT 303 Report"

    def _get_export_conf(self):
        try:
            return self.env.ref(
                'l10n_es_aeat_mod303.'
                'aeat_mod303_2017_main_export_config').id
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
            report.casilla_46 = (report.total_devengado -
                                 report.total_deducir)

    @api.depends("potential_cuota_compensar", "cuota_compensar")
    def _compute_remaining_cuota_compensar(self):
        for record in self:
            record.remaining_cuota_compensar = (
                record.potential_cuota_compensar - record.cuota_compensar
            )

    @api.multi
    @api.depends('porcentaje_atribuible_estado', 'casilla_46')
    def _compute_atribuible_estado(self):
        for report in self:
            report.atribuible_estado = (
                report.casilla_46 *
                report.porcentaje_atribuible_estado / 100)

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

    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Currency',
        related='company_id.currency_id', store=True, readonly=True)
    number = fields.Char(default='303')
    export_config = fields.Many2one(default=_get_export_conf)
    company_partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        relation='company_id.partner_id',
        store=True)
    devolucion_mensual = fields.Boolean(
        string="Devolución mensual",
        states={'done': [('readonly', True)]},
        help="Inscrito en el Registro de Devolución Mensual")
    total_devengado = fields.Float(
        string="[27] IVA devengado", readonly=True,
        compute="_compute_total_devengado", store=True)
    total_deducir = fields.Float(
        string="[45] IVA a deducir", readonly=True,
        compute="_compute_total_deducir", store=True)
    casilla_46 = fields.Float(
        string="[46] Resultado régimen general", readonly=True,
        store=True,
        help="(IVA devengado - IVA deducible)",
        compute="_compute_casilla_46")
    porcentaje_atribuible_estado = fields.Float(
        string="[65] % atribuible al Estado",
        states={'done': [('readonly', True)]},
        help="Los sujetos pasivos que tributen conjuntamente a la "
             "Administración del Estado y a las Diputaciones Forales "
             "del País Vasco o a la Comunidad Foral de Navarra, "
             "consignarán en esta casilla el porcentaje del volumen "
             "de operaciones en territorio común. Los demás sujetos "
             "pasivos consignarán en esta casilla el 100%", default=100)
    atribuible_estado = fields.Float(
        string="[66] Attributable to the Administration", readonly=True,
        compute='_compute_atribuible_estado', store=True)
    potential_cuota_compensar = fields.Float(
        string="[110] Pending fees to compensate", default=0,
        states={'done': [('readonly', True)]},
    )
    cuota_compensar = fields.Float(
        string="[78] Applied fees to compensate (old [67])", default=0,
        states={'done': [('readonly', True)]},
        help="Fee to compensate for prior periods, in which his statement "
             "was to return and compensation back option was chosen")
    remaining_cuota_compensar = fields.Float(
        string="[87] Remaining fees to compensate",
        compute="_compute_remaining_cuota_compensar",
    )
    regularizacion_anual = fields.Float(
        string="[68] Regularización anual",
        states={'done': [('readonly', True)]},
        help="En la última autoliquidación del año (la del período 4T "
             "o mes 12) se hará constar, con el signo que corresponda, "
             "el resultado de la regularización anual conforme "
             "disponen las Leyes por las que se aprueban el Concierto "
             "Económico entre el Estado y la Comunidad Autónoma del "
             "País Vasco y el Convenio Económico entre el Estado y la "
             "Comunidad Foral de Navarra.")
    casilla_69 = fields.Float(
        string="[69] Resultado", readonly=True,
        compute="_compute_casilla_69",
        help="Atribuible a la Administración [66] - Cuotas a "
             "compensar [67] + Regularización anual [68]""", store=True)
    casilla_77 = fields.Float(
        string="[77] Iva Diferido (Liquidado por aduana)",
        help="Se hará constar el importe de las cuotas del Impuesto "
             "a la importación incluidas en los documentos en los que "
             "conste la liquidación practicada por la Administración "
             "recibidos en el periodo de liquidación. Solamente podrá "
             "cumplimentarse esta casilla cuando se cumplan los "
             "requisitos establecidos en el artículo 74.1 del "
             "Reglamento del Impuesto sobre el Valor Añadido. ")
    previous_result = fields.Float(
        string="[70] A deducir",
        help="Resultado de la anterior o anteriores declaraciones del "
             "mismo concepto, ejercicio y periodo",
        states={'done': [('readonly', True)]})
    resultado_liquidacion = fields.Float(
        string="[71] Liquidación", readonly=True,
        compute="_compute_resultado_liquidacion", store=True)
    result_type = fields.Selection(
        selection=[('I', 'A ingresar'),
                   ('D', 'A devolver'),
                   ('C', 'A compensar'),
                   ('N', 'Sin actividad/Resultado cero')],
        compute="_compute_result_type")
    compensate = fields.Boolean(
        string="Compensate", states={'done': [('readonly', True)]},
        help="Si se marca, indicará que el importe a devolver se "
             "compensará en posteriores declaraciones")
    bank_account = fields.Many2one(
        comodel_name="res.partner.bank", string="Bank account",
        states={'done': [('readonly', True)]})
    counterpart_account = fields.Many2one(
        default=_default_counterpart_303)
    allow_posting = fields.Boolean(default=True)
    exonerated_390 = fields.Selection(
        selection=[
            ('1', u'Exonerado'),
            ('2', u'No exonerado'),
        ],
        default='2',
        required=True,
        states=NON_EDITABLE_ON_DONE,
        string=u"Exonerado mod. 390",
        help=u"Exonerado de la Declaración-resumen anual del IVA, modelo 390: "
             u"Volumen de operaciones (art. 121 LIVA)",
    )
    has_operation_volume = fields.Boolean(
        string=u"¿Volumen de operaciones?",
        default=True,
        states=NON_EDITABLE_ON_DONE,
        help=u"¿Existe volumen de operaciones (art. 121 LIVA)?",
    )
    has_347 = fields.Boolean(
        string=u"¿Obligación del 347?",
        default=True,
        states=NON_EDITABLE_ON_DONE,
        help=u"Marque la casilla si el sujeto pasivo ha efectuado con alguna "
             u"persona o entidad operaciones por las que tenga obligación de "
             u"presentar la declaración anual de operaciones con terceras "
             u"personas (modelo 347).",
    )
    is_voluntary_sii = fields.Boolean(
        string=u"¿SII voluntario?",
        states=NON_EDITABLE_ON_DONE,
        help=u"¿Ha llevado voluntariamente los Libros registro del IVA a "
             u"través de la Sede electrónica de la AEAT durante el ejercicio?",
    )
    main_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string=u"Código actividad principal",
    )
    main_activity_iae = fields.Char(
        states=NON_EDITABLE_ON_DONE,
        string=u"Epígrafe I.A.E. actividad principal",
        size=4,
    )
    other_first_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string=u"Código 1ª actividad",
    )
    other_first_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. 1ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    other_second_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string=u"Código 2ª actividad",
    )
    other_second_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. 2ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    other_third_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string=u"Código 3ª actividad",
    )
    other_third_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. 3ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    other_fourth_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string=u"Código 4ª actividad",
    )
    other_fourth_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. 4ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    other_fifth_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string=u"Código 5ª actividad",
    )
    other_fifth_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. 5ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    casilla_88 = fields.Float(
        string=u"[88] Total volumen operaciones",
        compute='_compute_casilla_88',
        help=u"Información adicional - Operaciones realizadas en el ejercicio"
             u" - Total volumen de operaciones ([80]+[81]+[93]+[94]+[83]+[84]"
             u"+[125]+[126]+[127]+[128]+[86]+[95]+[96]+[97]+[98]-[79]-[99])",
        store=True)
    marca_sepa = fields.Selection(
        selection=[
            ("0", "0 Vacía"),
            ("1", "1 Cuenta España"),
            ("2", "2 Unión Europea SEPA"),
            ("3", "3 Resto Países"),
        ],
        compute='_compute_marca_sepa')

    @api.depends("partner_bank_id", "result_type")
    def _compute_marca_sepa(self):
        for record in self:
            if record.result_type != 'D':
                record.marca_sepa = '0'
            elif record.partner_bank_id.bank.country == \
                    self.env.ref("base.es"):
                record.marca_sepa = "1"
            elif record.partner_bank_id.bank.country in \
                    self.env.ref("base.europe").country_ids:
                record.marca_sepa = "2"
            elif record.partner_bank_id.bank.country:
                record.marca_sepa = "3"
            else:
                record.marca_sepa = "0"

    def __init__(self, pool, cr):
        self._aeat_number = '303'
        super(L10nEsAeatMod303Report, self).__init__(pool, cr)

    @api.depends('tax_lines', 'tax_lines.amount')
    def _compute_casilla_88(self):
        for report in self:
            report.casilla_88 = sum(
                report.tax_lines.filtered(lambda x: x.field_number in (
                    80, 81, 83, 84, 85, 86, 93, 94, 95, 96, 97, 98, 125, 126,
                    127, 128
                )).mapped('amount')
            ) - sum(
                report.tax_lines.filtered(lambda x: x.field_number in (
                    79, 99,
                )).mapped('amount')
            )

    @api.multi
    def _compute_allow_posting(self):
        for report in self:
            report.allow_posting = True

    @api.multi
    @api.depends('resultado_liquidacion')
    def _compute_result_type(self):
        for report in self:
            if report.resultado_liquidacion == 0:
                report.result_type = 'N'
            elif report.resultado_liquidacion > 0:
                report.result_type = 'I'
            else:
                if report.devolucion_mensual:
                    report.result_type = 'D'
                else:
                    report.result_type = 'C'

    @api.onchange('period_type', 'fiscalyear_id')
    def onchange_period_type(self):
        super(L10nEsAeatMod303Report, self).onchange_period_type()
        if self.period_type not in ('4T', '12'):
            self.regularizacion_anual = 0
            self.exonerated_390 = '2'
        if (not self.fiscalyear_id or
                self.fiscalyear_id.date_start < '2018-01-01'):
            self.export_config = self.env.ref(
                'l10n_es_aeat_mod303.'
                'aeat_mod303_2017_main_export_config')
        else:
            self.export_config = self.env.ref(
                'l10n_es_aeat_mod303.'
                'aeat_mod303_2018_main_export_config')

    @api.onchange('type')
    def onchange_type(self):
        if self.type != 'C':
            self.previous_result = 0

    @api.onchange('result_type')
    def onchange_result_type(self):
        if self.result_type != 'C':
            self.compensate = False

    @api.multi
    def button_confirm(self):
        """Check records"""
        msg = ""
        for mod303 in self:
            if mod303.result_type == 'I' and not mod303.bank_account:
                msg = _('Select an account for making the charge')
            if mod303.result_type == 'D' and not mod303.bank_account:
                msg = _('Select an account for receiving the money')
        if msg:
            # Don't raise error, because data is not used
            # raise exceptions.Warning(msg)
            pass
        return super(L10nEsAeatMod303Report, self).button_confirm()

    @api.multi
    def _get_tax_code_lines(self, codes, periods=None, include_children=True):
        """Don't populate results for fields 79-99 for reports different from
        last of the year one or when not exonerated of presenting model 390.
        """
        if 79 <= self.env.context.get('field_number', 0) <= 99 or \
                self.env.context.get('field_number', 0) == 125:
            if (self.exonerated_390 == '2' or not self.has_operation_volume
                    or self.period_type not in ('4T', '12')):
                return self.env['account.move.line']
        return super(L10nEsAeatMod303Report, self)._get_tax_code_lines(
            codes, periods=periods, include_children=include_children,
        )

    @api.multi
    def _get_move_line_domain(self, codes, periods=None,
                              include_children=True):
        """Changes periods to full year when the summary on last report of the
        year for the corresponding fields. Only field number is checked as
        the complete check for not bringing results is done on
        `_get_tax_code_lines`.
        """
        if 79 <= self.env.context.get('field_number', 0) <= 99 or \
                self.env.context.get('field_number', 0) == 125:
            fiscalyear_code = fields.Date.from_string(
                periods[:1].date_stop
            ).year
            date_start = "%s-01-01" % fiscalyear_code
            date_stop = "%s-12-31" % fiscalyear_code
            periods = self.env["account.period"].search([
                ('date_start', '>=', date_start),
                ('date_stop', '<=', date_stop),
                ('special', '=', False)
            ])
        return super(L10nEsAeatMod303Report, self)._get_move_line_domain(
            codes, periods=periods, include_children=include_children,
        )


class L10nEsAeatMod303ReportActivityCode(models.Model):
    _name = "l10n.es.aeat.mod303.report.activity.code"
    _order = "period_type,code,id"

    period_type = fields.Selection(
        selection=[
            ('4T', '4T'),
            ('12', 'December'),
        ],
        required=True,
    )
    code = fields.Integer(
        string="Activity code",
        required=True,
    )
    name = fields.Char(
        string="Activity name",
        translate=True,
        required=True,
    )
