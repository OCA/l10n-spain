# Copyright 2013 - Guadaltech - Alberto Martín Cortada
# Copyright 2015 - AvanzOSC - Ainara Galdona
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2014-2021 Tecnativa - Pedro M. Baeza
# Copyright 2020 Sygel - Valentin Vinagre
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, exceptions, fields, models

_ACCOUNT_PATTERN_MAP = {
    "C": "4700",
    "D": "4700",
    "N": "4700",
    "I": "4750",
}

NON_EDITABLE_ON_DONE = {"done": [("readonly", True)]}
NON_EDITABLE_EXCEPT_DRAFT = {
    "done": [("readonly", True)],
    "calculated": [("readonly", True)],
    "posted": [("readonly", True)],
    "cancelled": [("readonly", True)],
}
EDITABLE_ON_DRAFT = {"draft": [("readonly", False)]}


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod303.report"
    _description = "AEAT 303 Report"
    _aeat_number = "303"

    devolucion_mensual = fields.Boolean(
        string="Montly Return",
        states=NON_EDITABLE_ON_DONE,
        help="Registered in the Register of Monthly Return",
    )
    total_devengado = fields.Float(
        string="[27] VAT payable",
        readonly=True,
        compute_sudo=True,
        compute="_compute_total_devengado",
        store=True,
    )
    total_deducir = fields.Float(
        string="[45] VAT receivable",
        readonly=True,
        compute_sudo=True,
        compute="_compute_total_deducir",
        store=True,
    )
    casilla_46 = fields.Float(
        string="[46] General scheme result",
        readonly=True,
        store=True,
        help="(VAT payable - VAT receivable)",
        compute="_compute_casilla_46",
    )
    porcentaje_atribuible_estado = fields.Float(
        string="[65] % attributable to State",
        default=100,
        states=NON_EDITABLE_ON_DONE,
        help="Taxpayers who pay jointly to the Central Government and "
        "the Provincial Councils of the Basque Country or the "
        "Autonomous Community of Navarra, will enter in this box the "
        "percentage of volume operations in the common territory. "
        "Other taxpayers will enter in this box 100%",
    )
    atribuible_estado = fields.Float(
        string="[66] Attributable to the Administration",
        readonly=True,
        compute="_compute_atribuible_estado",
        store=True,
    )
    potential_cuota_compensar = fields.Float(
        string="[110] Pending fees to compensate",
        default=0,
        states=NON_EDITABLE_ON_DONE,
    )
    cuota_compensar = fields.Float(
        string="[78] Applied fees to compensate (old [67])",
        default=0,
        states=NON_EDITABLE_ON_DONE,
        help="Fee to compensate for prior periods, in which his statement "
        "was to return and compensation back option was chosen",
    )
    remaining_cuota_compensar = fields.Float(
        string="[87] Remaining fees to compensate",
        compute="_compute_remaining_cuota_compensar",
    )
    regularizacion_anual = fields.Float(
        string="[68] Annual regularization",
        states=NON_EDITABLE_ON_DONE,
        compute="_compute_regularizacion_anual",
        readonly=False,
        store=True,
        help="In the last auto settlement of the year, shall be recorded "
        "(the fourth period or 12th month), with the appropriate sign, "
        "the result of the annual adjustment as have the laws by the "
        "Economic Agreement approved between the State and the "
        "Autonomous Community the Basque Country and the "
        "Economic Agreement between the State and Navarre.",
    )
    casilla_69 = fields.Float(
        string="[69] Result",
        readonly=True,
        compute="_compute_casilla_69",
        help="[66] Attributable to the Administration - "
        "[67] Fees to compensate + "
        "[68] Annual regularization",
        store=True,
    )
    casilla_77 = fields.Float(
        string="[77] VAT deferred (Settle by customs)",
        help="Contributions of import tax included in the documents "
        "evidencing the payment made by the Administration and received "
        "in the settlement period. You can only complete this box "
        "when the requirements of Article 74.1 of the Tax Regulations "
        "Value Added are met.",
    )
    previous_result = fields.Float(
        string="[70] To be deducted",
        help="Result of the previous or prior statements of the same concept, "
        "exercise and period",
        states=NON_EDITABLE_ON_DONE,
    )
    resultado_liquidacion = fields.Float(
        string="[71] Settlement result",
        readonly=True,
        compute="_compute_resultado_liquidacion",
        store=True,
    )
    result_type = fields.Selection(
        selection=[
            ("I", "To enter"),
            ("D", "To return"),
            ("C", "To compensate"),
            ("N", "No activity/Zero result"),
        ],
        string="Result type",
        compute="_compute_result_type",
    )
    counterpart_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Counterpart account",
        compute="_compute_counterpart_account_id",
        domain="[('company_id', '=', company_id)]",
        store=True,
        readonly=False,
    )
    allow_posting = fields.Boolean(string="Allow posting", default=True)
    exonerated_390 = fields.Selection(
        selection=[("1", u"Exonerado"), ("2", u"No exonerado")],
        default="2",
        required=True,
        states=NON_EDITABLE_EXCEPT_DRAFT,
        compute="_compute_exonerated_390",
        store=True,
        readonly=False,
        string=u"Exonerado mod. 390",
        help=u"Exonerado de la Declaración-resumen anual del IVA, modelo 390: "
        u"Volumen de operaciones (art. 121 LIVA)",
    )
    has_operation_volume = fields.Boolean(
        string=u"¿Volumen de operaciones?",
        default=True,
        readonly=True,
        states=EDITABLE_ON_DRAFT,
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
        string=u"Epígrafe I.A.E. 1ª actividad", states=NON_EDITABLE_ON_DONE, size=4,
    )
    other_second_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string=u"Código 2ª actividad",
    )
    other_second_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. 2ª actividad", states=NON_EDITABLE_ON_DONE, size=4,
    )
    other_third_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string=u"Código 3ª actividad",
    )
    other_third_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. 3ª actividad", states=NON_EDITABLE_ON_DONE, size=4,
    )
    other_fourth_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string=u"Código 4ª actividad",
    )
    other_fourth_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. 4ª actividad", states=NON_EDITABLE_ON_DONE, size=4,
    )
    other_fifth_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string=u"Código 5ª actividad",
    )
    other_fifth_activity_iae = fields.Char(
        string=u"Epígrafe I.A.E. 5ª actividad", states=NON_EDITABLE_ON_DONE, size=4,
    )
    casilla_88 = fields.Float(
        string=u"[88] Total volumen operaciones",
        compute="_compute_casilla_88",
        help=u"Información adicional - Operaciones realizadas en el ejercicio"
        u" - Total volumen de operaciones ([80]+[81]+[93]+[94]+[83]+[84]"
        u"+[125]+[126]+[127]+[128]+[86]+[95]+[96]+[97]+[98]-[79]-[99])",
        store=True,
    )
    marca_sepa = fields.Selection(
        selection=[
            ("0", "0 Vacía"),
            ("1", "1 Cuenta España"),
            ("2", "2 Unión Europea SEPA"),
            ("3", "3 Resto Países"),
        ],
        compute="_compute_marca_sepa",
    )

    @api.depends("partner_bank_id", "result_type")
    def _compute_marca_sepa(self):
        for record in self:
            if record.result_type != "D":
                record.marca_sepa = "0"
            elif record.partner_bank_id.bank_id.country == self.env.ref("base.es"):
                record.marca_sepa = "1"
            elif (
                record.partner_bank_id.bank_id.country
                in self.env.ref("base.europe").country_ids
            ):
                record.marca_sepa = "2"
            elif record.partner_bank_id.bank_id.country:
                record.marca_sepa = "3"
            else:
                record.marca_sepa = "0"

    @api.depends("date_start", "cuota_compensar")
    def _compute_exception_msg(self):
        super(L10nEsAeatMod303Report, self)._compute_exception_msg()
        for mod303 in self.filtered(lambda x: x.state != "draft"):
            # Get result from previous declarations, in order to identify if
            # there is an amount to compensate.
            prev_reports = mod303._get_previous_fiscalyear_reports(
                mod303.date_start
            ).filtered(lambda x: x.state not in ["draft", "cancelled"])
            if not prev_reports:
                continue
            prev_report = min(
                prev_reports,
                key=lambda x: abs(
                    fields.Date.to_date(x.date_end)
                    - fields.Date.to_date(mod303.date_start)
                ),
            )
            if prev_report.result_type == "C" and not mod303.cuota_compensar:
                if mod303.exception_msg:
                    mod303.exception_msg += "\n"
                else:
                    mod303.exception_msg = ""
                mod303.exception_msg += _(
                    "In previous declarations this year you reported a "
                    "Result Type 'To Compensate'. You might need to fill "
                    "field '[67] Fees to compensate' in this declaration."
                )

    @api.depends("company_id", "result_type")
    def _compute_counterpart_account_id(self):
        for record in self:
            code = ("%s%%" % _ACCOUNT_PATTERN_MAP.get(record.result_type, "4750"),)
            record.counterpart_account_id = self.env["account.account"].search(
                [("code", "=like", code[0]), ("company_id", "=", record.company_id.id)],
                limit=1,
            )

    @api.depends("period_type")
    def _compute_regularizacion_anual(self):
        for record in self:
            if record.period_type not in ("4T", "12"):
                record.regularizacion_anual = 0

    @api.depends("period_type")
    def _compute_exonerated_390(self):
        for record in self:
            if record.period_type not in ("4T", "12"):
                record.exonerated_390 = "2"

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_total_devengado(self):
        casillas_devengado = (3, 6, 9, 11, 13, 15, 18, 21, 24, 26)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas_devengado
            )
            report.total_devengado = sum(tax_lines.mapped("amount"))

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_total_deducir(self):
        casillas_deducir = (29, 31, 33, 35, 37, 39, 41, 42, 43, 44)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas_deducir
            )
            report.total_deducir = sum(tax_lines.mapped("amount"))

    @api.depends("total_devengado", "total_deducir")
    def _compute_casilla_46(self):
        for report in self:
            report.casilla_46 = report.total_devengado - report.total_deducir

    @api.depends("porcentaje_atribuible_estado", "casilla_46")
    def _compute_atribuible_estado(self):
        for report in self:
            report.atribuible_estado = (
                report.casilla_46 * report.porcentaje_atribuible_estado / 100.0
            )

    @api.depends("potential_cuota_compensar", "cuota_compensar")
    def _compute_remaining_cuota_compensar(self):
        for record in self:
            record.remaining_cuota_compensar = (
                record.potential_cuota_compensar - record.cuota_compensar
            )

    @api.depends(
        "atribuible_estado", "cuota_compensar", "regularizacion_anual", "casilla_77"
    )
    def _compute_casilla_69(self):
        for report in self:
            report.casilla_69 = (
                report.atribuible_estado
                + report.casilla_77
                - report.cuota_compensar
                + report.regularizacion_anual
            )

    @api.depends("casilla_69", "previous_result")
    def _compute_resultado_liquidacion(self):
        for report in self:
            report.resultado_liquidacion = report.casilla_69 - report.previous_result

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_88(self):
        for report in self:
            report.casilla_88 = sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number
                    in (
                        80,
                        81,
                        83,
                        84,
                        85,
                        86,
                        93,
                        94,
                        95,
                        96,
                        97,
                        98,
                        125,
                        126,
                        127,
                        128,
                    )
                ).mapped("amount")
            ) - sum(
                report.tax_line_ids.filtered(
                    lambda x: x.field_number in (79, 99,)
                ).mapped("amount")
            )

    def _compute_allow_posting(self):
        for report in self:
            report.allow_posting = True

    @api.depends(
        "resultado_liquidacion", "period_type", "devolucion_mensual",
    )
    def _compute_result_type(self):
        for report in self:
            if report.resultado_liquidacion == 0:
                report.result_type = "N"
            elif report.resultado_liquidacion > 0:
                report.result_type = "I"
            else:
                if report.devolucion_mensual or report.period_type in ("4T", "12"):
                    report.result_type = "D"
                else:
                    report.result_type = "C"

    @api.onchange("statement_type")
    def onchange_type(self):
        if self.statement_type != "C":
            self.previous_result = 0

    def calculate(self):
        res = super(L10nEsAeatMod303Report, self).calculate()
        for mod303 in self:
            prev_reports = mod303._get_previous_fiscalyear_reports(
                mod303.date_start
            ).filtered(lambda x: x.state not in ["draft", "cancelled"])
            if not prev_reports:
                continue
            prev_report = min(
                prev_reports,
                key=lambda x: abs(
                    fields.Date.to_date(x.date_end)
                    - fields.Date.to_date(mod303.date_start)
                ),
            )
            if prev_report.result_type == "C":
                amount = abs(prev_report.resultado_liquidacion)
                mod303.write(
                    {"cuota_compensar": amount, "potential_cuota_compensar": amount}
                )
        return res

    def button_confirm(self):
        """Check records"""
        msg = ""
        for mod303 in self:
            if mod303.result_type == "D" and not mod303.partner_bank_id:
                msg = _("Select an account for receiving the money")
        if msg:
            raise exceptions.Warning(msg)
        return super(L10nEsAeatMod303Report, self).button_confirm()

    @api.constrains("potential_cuota_compensar", "cuota_compensar")
    def check_qty(self):
        if self.filtered(
            lambda x: (
                x.cuota_compensar < 0
                or x.remaining_cuota_compensar < 0
                or (x.potential_cuota_compensar - x.cuota_compensar) < 0
            )
        ):
            raise exceptions.ValidationError(
                _("The fee to compensate must be indicated as a positive number.")
            )

    def _get_tax_lines(self, date_start, date_end, map_line):
        """Don't populate results for fields 79-99 for reports different from
        last of the year one or when not exonerated of presenting model 390.
        """
        if 79 <= map_line.field_number <= 99 or map_line.field_number == 125:
            if (
                self.exonerated_390 == "2"
                or not self.has_operation_volume
                or self.period_type not in ("4T", "12")
            ):
                return self.env["account.move.line"]
        return super(L10nEsAeatMod303Report, self)._get_tax_lines(
            date_start, date_end, map_line,
        )

    def _get_move_line_domain(self, date_start, date_end, map_line):
        """Changes dates to full year when the summary on last report of the
        year for the corresponding fields. Only field number is checked as
        the complete check for not bringing results is done on
        `_get_tax_lines`.
        """
        if 79 <= map_line.field_number <= 99 or map_line.field_number == 125:
            date_start = date_start.replace(day=1, month=1)
            date_end = date_end.replace(day=31, month=12)
        return super(L10nEsAeatMod303Report, self)._get_move_line_domain(
            date_start, date_end, map_line,
        )


class L10nEsAeatMod303ReportActivityCode(models.Model):
    _name = "l10n.es.aeat.mod303.report.activity.code"
    _order = "period_type,code,id"
    _description = "AEAT 303 Report Activities Codes"

    period_type = fields.Selection(
        selection=[("4T", "4T"), ("12", "December")], required=True,
    )
    code = fields.Integer(string="Activity code", required=True,)
    name = fields.Char(string="Activity name", translate=True, required=True,)
