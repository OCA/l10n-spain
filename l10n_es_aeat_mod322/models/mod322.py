# Copyright 2022 QubiQ - Jan Tugores
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, exceptions, fields, models

NON_EDITABLE_ON_DONE = {"done": [("readonly", True)]}
NON_EDITABLE_EXCEPT_DRAFT = {
    "done": [("readonly", True)],
    "calculated": [("readonly", True)],
    "posted": [("readonly", True)],
    "cancelled": [("readonly", True)],
}
EDITABLE_ON_DRAFT = {"draft": [("readonly", False)]}

_ACCOUNT_PATTERN_MAP = {
    "C": "4700",
    "D": "4700",
    "N": "4700",
    "I": "4750",
}


class L10nEsAeatMod322Report(models.Model):
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod322.report"
    _description = "AEAT 322 Report"
    _aeat_number = "322"

    def _get_dominant_company_vat(self):
        company = self.env.company
        if company.parent_id:
            company = company.parent_id
        return company.vat or ""

    def _get_group_number(self):
        return self.env.company.group_number or ""

    company_type = fields.Selection(
        string="Tipo de compañía",
        selection=[
            ("D", "Dominante"),
            ("P", "Dependiente"),
        ],
        compute="_compute_company_type",
        states=EDITABLE_ON_DRAFT,
        store=True,
        required=True,
    )
    dominant_company_vat = fields.Char(
        string="NIF de la entidad dominante",
        default=_get_dominant_company_vat,
        states=EDITABLE_ON_DRAFT,
        required=True,
    )
    group_number = fields.Char(
        string="Nº Grupo",
        default=_get_group_number,
        states=EDITABLE_ON_DRAFT,
        required=True,
    )
    aplicable_special_regime = fields.Boolean(
        string="Tipo régimen especial aplicable",
        states=NON_EDITABLE_ON_DONE,
        help="Tipo régimen especial aplicable: Art. 163 sexies.Cinco LIVA",
    )
    monthly_return_record = fields.Boolean(
        string="Registro de devolución mensual",
        states=NON_EDITABLE_ON_DONE,
        help="¿Está inscrito en el Registro de devolución mensual " "(Art. 30 RIVA)?",
    )
    special_cash_criterion_regime = fields.Boolean(
        string="Régimen especial del criterio de caja",
        states=NON_EDITABLE_ON_DONE,
        help="¿Es destinatario de operaciones a las que se aplique el régimen "
        "especial del criterio de caja?",
    )
    aplicable_special_prorate = fields.Boolean(
        string="Aplicación de la prorrata especial",
        states=NON_EDITABLE_ON_DONE,
        help="Opción por la aplicación de la prorrata especial "
        "(artículo 103.Dos.1º LIVA)",
    )
    aplicable_special_prorate_revocation = fields.Boolean(
        string="Revocación de aplicación de la prorrata especial",
        states=NON_EDITABLE_ON_DONE,
        help="Revocación de la opción por la aplicación de la prorrata "
        "especial (artículo 103.Dos.1º LIVA)",
    )
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
    total_earned = fields.Float(
        string="[38] Total cuota devengada",
        readonly=True,
        compute_sudo=True,
        compute="_compute_total_earned",
        store=True,
        help="Total cuota devengada ([03]+[06]+[09]+[11]+[14]+[17]+[20]+[22]+"
        "[24]+[26]+[29]+[32]+[35]+[37])",
    )
    total_to_deduct = fields.Float(
        string="[62] Total a deducir",
        readonly=True,
        compute_sudo=True,
        compute="_compute_total_to_deduct",
        store=True,
        help="Total a deducir ([40]+[42]+[44]+[46]+[48]+[50]+[52]+[54]+[56]+"
        "[58]+[59]+[60]+[61])",
    )
    field_63 = fields.Float(
        string="[63] Diferencia ([38] - [62] + [76])",
        readonly=True,
        compute_sudo=True,
        compute="_compute_field_63",
        store=True,
    )
    state_percentage_attributable = fields.Integer(
        string="[64] % Atribuible a la Administración del Estado",
        default=100,
        states=NON_EDITABLE_ON_DONE,
    )
    state_attributable = fields.Float(
        string="[65] Atribuible a la Administración del Estado",
        readonly=True,
        compute="_compute_state_attributable",
        store=True,
    )
    field_77 = fields.Float(
        string="[77] IVA diferido (Liquidar en aduana)",
        help="[77] IVA a la importación liquidado por la Aduana pendiente "
        "de ingreso",
    )
    field_66 = fields.Float(
        string="[66] Cuotas a compensar anteriores al grupo",
        default=0,
        states=NON_EDITABLE_ON_DONE,
        help="[66] Cuotas a compensar de períodos anteriores a la "
        "incorporación al grupo",
    )
    annual_regularization = fields.Float(
        string="[67] Resultado de la regularización anual",
        states=NON_EDITABLE_ON_DONE,
        compute="_compute_annual_regularization",
        readonly=True,
        store=True,
        help="[67] Exclusivamente para sujetos pasivos que tributan "
        "conjuntamente a la Administración del Estado y a las Diputaciones "
        "Forales. Resultado de la regularización anual.",
    )
    field_68 = fields.Float(
        string="[68] Resultado ([65] + [77] - [66] + [67])",
        readonly=True,
        compute_sudo=True,
        compute="_compute_field_68",
        store=True,
    )
    previous_result = fields.Float(
        string="[69] A deducir",
        states=NON_EDITABLE_ON_DONE,
        help="[69] Resultado de las autoliquidaciones anteriores "
        "presentadas por el mismo concepto, ejercicio y periodo",
    )
    selfsettlement_result = fields.Float(
        string="[70] Resultado de la autoliquidación ([68] - [69])",
        readonly=True,
        compute="_compute_selfsettlement_result",
        store=True,
    )
    complementary_selfsettlement = fields.Boolean(
        string="Autoliquidación complementaria",
        states=NON_EDITABLE_ON_DONE,
    )
    previous_selfsettlement_recipt = fields.Char(
        string="Justificante de la autoliquidación anterior",
        states=NON_EDITABLE_ON_DONE,
        size=13,
        help="En el supuesto caso que esta sea una autoliquidacón "
        "complementária, se hará constar también en este apartado el número "
        "identificativo de 13 dígitos de la autoliquidación anterior. De "
        "haberse presentado anteriormente más de una declaración, se hará "
        "constar el número identificativo de la última de ellas.",
    )
    without_activity = fields.Boolean(
        string="Sin actividad",
        states=NON_EDITABLE_ON_DONE,
        help="Si no se han devengado ni soportado cuotas durante el período a "
        "que se refiere la presente declaración marque con una “X” esta "
        "casilla.",
    )
    main_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod322.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string="Código actividad principal",
    )
    main_activity_iae = fields.Char(
        states=NON_EDITABLE_ON_DONE,
        string="Epígrafe I.A.E. actividad principal",
        size=4,
    )
    other_first_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod322.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string="Código 1ª actividad",
    )
    other_first_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 1ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    other_second_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod322.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string="Código 2ª actividad",
    )
    other_second_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 2ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    other_third_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod322.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string="Código 3ª actividad",
    )
    other_third_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 3ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    other_fourth_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod322.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string="Código 4ª actividad",
    )
    other_fourth_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 4ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    other_fifth_activity_code = fields.Many2one(
        comodel_name="l10n.es.aeat.mod322.report.activity.code",
        domain="[('period_type', '=', period_type)]",
        states=NON_EDITABLE_ON_DONE,
        string="Código 5ª actividad",
    )
    other_fifth_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 5ª actividad",
        states=NON_EDITABLE_ON_DONE,
        size=4,
    )
    field_88 = fields.Float(
        string="[88] Total volumen operaciones",
        compute="_compute_field_88",
        help="Información adicional - Operaciones realizadas en el ejercicio"
        " - Total volumen de operaciones ([80]+[81]+[93]+[94]+[83]+[84]"
        "+[125]+[126]+[127]+[128]+[86]+[95]+[96]+[97]+[98]-[79]-[99])",
        store=True,
    )
    result_type = fields.Selection(
        selection=[
            ("I", "To enter"),
            ("D", "To return"),
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

    @api.depends("company_id")
    def _compute_company_type(self):
        if self.company_id.parent_id:
            self.company_type = "P"
        else:
            self.company_type = "D"

    @api.onchange("company_id")
    def _onchange_company_id(self):
        if self.company_id.parent_id:
            company = self.company_id.parent_id
        else:
            company = self.company_id
        self.dominant_company_vat = company.vat

        self.group_number = self.company_id.group_number

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_total_earned(self):
        earned = (3, 6, 9, 11, 14, 17, 20, 22, 24, 26, 29, 32, 35, 37)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(lambda x: x.field_number in earned)
            report.total_earned = sum(tax_lines.mapped("amount"))

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_total_to_deduct(self):
        to_deduct = (40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 59, 60, 61)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in to_deduct
            )
            report.total_to_deduct = sum(tax_lines.mapped("amount"))

    @api.depends("period_type")
    def _compute_exonerated_390(self):
        for record in self:
            if record.period_type not in ("4T", "12"):
                record.exonerated_390 = "2"

    @api.depends("total_earned", "total_to_deduct")
    def _compute_field_63(self):
        for sel in self:
            sel.field_63 = sel.total_earned - sel.total_to_deduct

    @api.depends("state_percentage_attributable", "field_63")
    def _compute_state_attributable(self):
        for report in self:
            report.state_attributable = (
                report.field_63 * report.state_percentage_attributable / 100.0
            )

    @api.depends("period_type")
    def _compute_annual_regularization(self):
        for record in self:
            if record.period_type not in ("4T", "12"):
                record.annual_regularization = 0

    @api.depends("state_attributable", "field_77", "field_66", "annual_regularization")
    def _compute_field_68(self):
        for report in self:
            report.field_68 = (
                report.state_attributable
                + report.field_77
                - report.field_66
                + report.annual_regularization
            )

    @api.depends("field_68", "previous_result")
    def _compute_selfsettlement_result(self):
        for sel in self:
            sel.selfsettlement_result = sel.field_68 - sel.previous_result

    def _compute_field_88(self):
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
                    lambda x: x.field_number in (79, 99)
                ).mapped("amount")
            )

    def _compute_allow_posting(self):
        for report in self:
            report.allow_posting = True

    @api.depends("company_id", "result_type")
    def _compute_counterpart_account_id(self):
        for record in self:
            code = ("%s%%" % _ACCOUNT_PATTERN_MAP.get(record.result_type, "4750"),)
            record.counterpart_account_id = self.env["account.account"].search(
                [("code", "=like", code[0]), ("company_id", "=", record.company_id.id)],
                limit=1,
            )

    @api.depends(
        "selfsettlement_result",
        "period_type",
        "monthly_return_record",
    )
    def _compute_result_type(self):
        for report in self:
            if report.selfsettlement_result == 0:
                report.result_type = "N"
            elif report.selfsettlement_result > 0:
                report.result_type = "I"
            else:
                if report.monthly_return_record or report.period_type in ("4T", "12"):
                    report.result_type = "D"
                else:
                    report.result_type = "C"

    @api.onchange("statement_type")
    def onchange_type(self):
        if self.statement_type != "C":
            self.previous_result = 0

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
        """
        Don't populate results for fields 79-99 for reports different from
        last of the year one or when not exonerated of presenting model 390.
        """
        if 79 <= map_line.field_number <= 99 or map_line.field_number == 125:
            if (
                self.exonerated_390 == "2"
                or not self.has_operation_volume
                or self.period_type not in ("4T", "12")
            ):
                return self.env["account.move.line"]
        return super()._get_tax_lines(date_start, date_end, map_line)

    def _get_move_line_domain(self, date_start, date_end, map_line):
        """
        Changes dates to full year when the summary on last report of the
        year for the corresponding fields. Only field number is checked as
        the complete check for not bringing results is done on
        `_get_tax_lines`.
        """
        if 79 <= map_line.field_number <= 99 or map_line.field_number == 125:
            date_start = date_start.replace(day=1, month=1)
            date_end = date_end.replace(day=31, month=12)
        return super()._get_move_line_domain(date_start, date_end, map_line)


class L10nEsAeatMod322ReportActivityCode(models.Model):
    _name = "l10n.es.aeat.mod322.report.activity.code"
    _order = "period_type,code,id"
    _description = "AEAT 322 Report Activities Codes"

    period_type = fields.Selection(
        selection=[("4T", "4T"), ("12", "December")],
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
