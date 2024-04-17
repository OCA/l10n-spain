# Copyright 2013 - Guadaltech - Alberto Martín Cortada
# Copyright 2015 - AvanzOSC - Ainara Galdona
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2020 Sygel - Valentin Vinagre
# Copyright 2014-2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, exceptions, fields, models
from odoo.tools import float_compare

_ACCOUNT_PATTERN_MAP = {
    "C": "4700",
    "D": "4700",
    "V": "4700",
    "X": "4700",
    "N": "4700",
    "I": "4750",
    "G": "4750",
    "U": "4750",
}
NON_EDITABLE_ON_DONE = {"done": [("readonly", True)]}
NON_EDITABLE_EXCEPT_DRAFT = {
    "done": [("readonly", True)],
    "calculated": [("readonly", True)],
    "posted": [("readonly", True)],
    "cancelled": [("readonly", True)],
}
EDITABLE_ON_DRAFT = {"draft": [("readonly", False)]}
ACTIVITY_CODE_DOMAIN = (
    "["
    "   '|',"
    "   ('period_type', '=', False), ('period_type', '=', period_type),"
    "   '&',"
    "   '|', ('date_start', '=', False), ('date_start', '<=', date_start),"
    "   '|', ('date_end', '=', False), ('date_end', '>=', date_end),"
    "]"
)


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
    return_last_period = fields.Boolean(
        string="Last Period Return",
        states=NON_EDITABLE_ON_DONE,
        help="Check if you are submitting the last period return",
        compute="_compute_return_last_period",
        store=True,
        readonly=False,
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
    use_aeat_account = fields.Boolean(
        "Usar cuenta corriente tributaria",
        help=(
            "Si está suscrito a la cuenta corriente en materia tributaria, "
            "active esta opción para usarla en el ingreso o devolución."
        ),
    )
    result_type = fields.Selection(
        selection=[
            ("I", "To enter"),
            ("G", "To enter - AEAT account"),
            ("U", "To enter - Bank account debit"),
            ("D", "To return"),
            ("V", "To return - AEAT account"),
            ("X", "To return - Foreign bank account"),
            ("C", "To compensate"),
            ("N", "No activity/Zero result"),
        ],
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
    allow_posting = fields.Boolean(default=True)
    exonerated_390 = fields.Selection(
        selection=[("1", "Exonerado"), ("2", "No exonerado")],
        default="2",
        required=True,
        states=NON_EDITABLE_EXCEPT_DRAFT,
        compute="_compute_exonerated_390",
        store=True,
        readonly=False,
        string="Exonerado mod. 390",
        help="Exonerado de la Declaración-resumen anual del IVA, modelo 390: "
        "Volumen de operaciones (art. 121 LIVA)",
    )
    has_operation_volume = fields.Boolean(
        string="¿Volumen de operaciones?",
        default=True,
        readonly=True,
        states=EDITABLE_ON_DRAFT,
        help="¿Existe volumen de operaciones (art. 121 LIVA)?",
    )
    has_347 = fields.Boolean(
        string="¿Obligación del 347?",
        default=True,
        states=NON_EDITABLE_ON_DONE,
        help="Marque la casilla si el sujeto pasivo ha efectuado con alguna "
        "persona o entidad operaciones por las que tenga obligación de "
        "presentar la declaración anual de operaciones con terceras "
        "personas (modelo 347).",
    )
    is_voluntary_sii = fields.Boolean(
        string="¿SII voluntario?",
        states=NON_EDITABLE_ON_DONE,
        help="¿Ha llevado voluntariamente los Libros registro del IVA a "
        "través de la Sede electrónica de la AEAT durante el ejercicio?",
    )
    main_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain=ACTIVITY_CODE_DOMAIN,
        states=NON_EDITABLE_ON_DONE,
        string="Código actividad principal",
    )
    main_activity_iae = fields.Char(
        states=NON_EDITABLE_ON_DONE,
        string="Epígrafe I.A.E. actividad principal",
        size=4,
    )
    other_first_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain=ACTIVITY_CODE_DOMAIN,
        states=NON_EDITABLE_ON_DONE,
        string="Código 1ª actividad",
    )
    other_first_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 1ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    other_second_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain=ACTIVITY_CODE_DOMAIN,
        states=NON_EDITABLE_ON_DONE,
        string="Código 2ª actividad",
    )
    other_second_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 2ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    other_third_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain=ACTIVITY_CODE_DOMAIN,
        states=NON_EDITABLE_ON_DONE,
        string="Código 3ª actividad",
    )
    other_third_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 3ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    other_fourth_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain=ACTIVITY_CODE_DOMAIN,
        states=NON_EDITABLE_ON_DONE,
        string="Código 4ª actividad",
    )
    other_fourth_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 4ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    other_fifth_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain=ACTIVITY_CODE_DOMAIN,
        states=NON_EDITABLE_ON_DONE,
        string="Código 5ª actividad",
    )
    other_fifth_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 5ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    casilla_88 = fields.Float(
        string="[88] Total volumen operaciones",
        compute="_compute_casilla_88",
        help="Información adicional - Operaciones realizadas en el ejercicio"
        " - Total volumen de operaciones ([80]+[81]+[93]+[94]+[83]+[84]"
        "+[125]+[126]+[127]+[128]+[86]+[95]+[96]+[97]+[98]-[79]-[99])",
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

    @api.depends("partner_bank_id", "use_aeat_account")
    def _compute_marca_sepa(self):
        for record in self:
            if record.use_aeat_account:
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

    # pylint:disable=missing-return
    @api.depends("date_start", "cuota_compensar")
    def _compute_exception_msg(self):
        super()._compute_exception_msg()
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

    @api.depends("period_type")
    def _compute_return_last_period(self):
        for record in self:
            if record.period_type not in ("4T", "12"):
                record.return_last_period = False

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_total_devengado(self):
        casillas_devengado = (152, 3, 155, 6, 9, 11, 13, 15, 158, 18, 21, 24, 26)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas_devengado
            )
            report.total_devengado = report.currency_id.round(
                sum(tax_lines.mapped("amount"))
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_total_deducir(self):
        casillas_deducir = (29, 31, 33, 35, 37, 39, 41, 42, 43, 44)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas_deducir
            )
            report.total_deducir = report.currency_id.round(
                sum(tax_lines.mapped("amount"))
            )

    @api.depends("total_devengado", "total_deducir")
    def _compute_casilla_46(self):
        for report in self:
            report.casilla_46 = report.currency_id.round(
                report.total_devengado - report.total_deducir
            )

    @api.depends("porcentaje_atribuible_estado", "casilla_46")
    def _compute_atribuible_estado(self):
        for report in self:
            report.atribuible_estado = report.currency_id.round(
                report.casilla_46 * report.porcentaje_atribuible_estado / 100.0
            )

    @api.depends("potential_cuota_compensar", "cuota_compensar")
    def _compute_remaining_cuota_compensar(self):
        for report in self:
            report.remaining_cuota_compensar = report.currency_id.round(
                report.potential_cuota_compensar - report.cuota_compensar
            )

    @api.depends(
        "atribuible_estado", "cuota_compensar", "regularizacion_anual", "casilla_77"
    )
    def _compute_casilla_69(self):
        for report in self:
            report.casilla_69 = report.currency_id.round(
                report.atribuible_estado
                + report.casilla_77
                - report.cuota_compensar
                + report.regularizacion_anual
            )

    @api.depends("casilla_69", "previous_result")
    def _compute_resultado_liquidacion(self):
        # TODO: Add field 109
        for report in self:
            report.resultado_liquidacion = report.currency_id.round(
                report.casilla_69 - report.previous_result
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_88(self):
        taxes_88 = (80, 81, 83, 84, 85, 86, 93, 94, 95, 96, 97, 98, 125, 126, 127, 128)
        for report in self:
            report.casilla_88 = report.currency_id.round(
                sum(
                    report.tax_line_ids.filtered(
                        lambda x: x.field_number in taxes_88
                    ).mapped("amount")
                )
                - sum(
                    report.tax_line_ids.filtered(
                        lambda x: x.field_number in (79, 99)
                    ).mapped("amount")
                )
            )

    def _compute_allow_posting(self):
        for report in self:
            report.allow_posting = True

    @api.depends(
        "resultado_liquidacion",
        "period_type",
        "devolucion_mensual",
        "marca_sepa",
        "use_aeat_account",
        "return_last_period",
    )
    def _compute_result_type(self):
        for report in self:
            result = float_compare(
                report.resultado_liquidacion,
                0,
                precision_digits=report.currency_id.decimal_places,
            )
            if result == 0:
                report.result_type = "N"
            elif result == 1:
                if report.use_aeat_account:
                    report.result_type = "G"
                elif report.marca_sepa in {"1", "2"}:
                    # Domiciliar ingreso porque se indicó un banco SEPA
                    report.result_type = "U"
                else:
                    report.result_type = "I"
            else:
                if report.devolucion_mensual or report.period_type in ("4T", "12"):
                    if report.use_aeat_account:
                        report.result_type = "V"
                    elif report.return_last_period:
                        report.result_type = "D" if report.marca_sepa == "1" else "X"
                    else:
                        report.result_type = "C"
                else:
                    report.result_type = "C"

    @api.onchange("statement_type")
    def onchange_type(self):
        if self.statement_type != "C":
            self.previous_result = 0

    def calculate(self):
        self.cuota_compensar = 0
        res = super().calculate()
        for mod303 in self:
            prev_reports = self.search(
                [("date_start", "<", mod303.date_start)]
            ).filtered(lambda m: m.state not in ["draft", "cancelled"])
            if prev_reports:
                prev_report = min(
                    prev_reports,
                    key=lambda x: abs(
                        fields.Date.to_date(x.date_end)
                        - fields.Date.to_date(mod303.date_start)
                    ),
                )
                if prev_report and (
                    prev_report.remaining_cuota_compensar > 0
                    or prev_report.result_type == "C"
                ):
                    mod303.write(
                        {
                            "potential_cuota_compensar": (
                                prev_report.remaining_cuota_compensar
                                - prev_report.resultado_liquidacion
                            ),
                        }
                    )
            if mod303.return_last_period:
                cuota_compensar = mod303.potential_cuota_compensar
            elif (
                float_compare(
                    mod303.resultado_liquidacion,
                    0,
                    precision_digits=mod303.currency_id.decimal_places,
                )
                != -1
            ):
                cuota_compensar = min(
                    mod303.potential_cuota_compensar, mod303.resultado_liquidacion
                )
            else:
                cuota_compensar = 0
            mod303.cuota_compensar = cuota_compensar

        return res

    def button_confirm(self):
        """Check records"""
        msg = ""
        for mod303 in self:
            if mod303.result_type == "D" and not mod303.partner_bank_id:
                msg = _("Select an account for receiving the money")
        if msg:
            raise exceptions.UserError(msg)
        return super().button_confirm()

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
        return super()._get_tax_lines(
            date_start,
            date_end,
            map_line,
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
        return super()._get_move_line_domain(
            date_start,
            date_end,
            map_line,
        )


class L10nEsAeatMod303ReportActivityCode(models.Model):
    _name = "l10n.es.aeat.mod303.report.activity.code"
    _order = "period_type,code,id"
    _description = "AEAT 303 Report Activities Codes"

    period_type = fields.Selection(selection=[("4T", "4T"), ("12", "December")])
    code = fields.Char(string="Activity code", required=True)
    name = fields.Char(
        string="Activity name",
        translate=True,
        required=True,
    )
    date_start = fields.Date(string="Starting date")
    date_end = fields.Date(string="Ending date")
