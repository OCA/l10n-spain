# Copyright 2014-2019 Tecnativa - Pedro M. Baeza

from odoo import _, api, exceptions, fields, models
from odoo.tools import float_compare


def trunc(f, n):
    slen = len("%.*f" % (n, f))
    return float(str(f)[:slen])


class L10nEsAeatMod130Report(models.Model):
    _description = "AEAT 130 report"
    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod130.report"
    _aeat_number = "130"

    activity_type = fields.Selection(
        [
            ("primary", "Actividad agrícola, ganadera, forestal o pesquera"),
            ("other", "Actividad distinta a las anteriores"),
        ],
        string="Tipo de actividad",
        states={"draft": [("readonly", False)]},
        readonly=True,
        required=True,
        default="other",
    )
    has_deduccion_80 = fields.Boolean(
        string="¿Deducción por art. 80 bis?",
        states={"draft": [("readonly", False)]},
        readonly=True,
        help="Permite indicar si puede beneficiarse de la deducción por "
        "obtención de rendimientos de actividades económicas a efectos del "
        "pago fraccionado por cumplir el siguiente requisito:\n Que, en el "
        "primer trimestre del ejercicio o en el primer trimestre de inicio de "
        "actividades, la suma del resultado de elevar al año el importe de la "
        "casilla 03 y/o, en su caso, el resultado de elevar al año el 25 por "
        "100 de la casilla 08, sea igual o inferior a 12.000 euros. En los "
        "supuestos de inicio de la actividad a lo largo del ejercicio en la "
        "elevación al año se tendrán en consideración los días que resten "
        "hasta el final del año.",
        default=False,
    )
    has_prestamo = fields.Boolean(
        string="¿Préstamo para vivienda habitual?",
        states={"draft": [("readonly", False)]},
        readonly=True,
        help="Permite indicar si destina cantidades al pago de préstamos "
        "para la adquisición o rehabilitación de la vivienda habitual. Si "
        "marca la casilla, se podrá realiza un 2% de deducción sobre el "
        "importe de la casilla [03], con un máximo de 660,14 € por trimestre, "
        "o del 2% de la casilla [08], con un máximo de 660,14 euros anuales. "
        "\nDebe consultar las excepciones para las que no se computaría "
        "la deducción a pesar del préstamo.",
        default=False,
    )
    comments = fields.Char(
        string="Observaciones",
        size=350,
        readonly=True,
        help="Observaciones que se adjuntarán con el modelo",
        states={"draft": [("readonly", False)]},
    )
    casilla_01 = fields.Monetary(
        string="Casilla [01] - Ingresos",
        readonly=True,
    )
    real_expenses = fields.Monetary(
        string="Gastos reales",
        help="Gastos en el periodo sin contar con el 5% adicional de difícil "
        "justificación.",
    )
    non_justified_expenses = fields.Monetary(
        string="Gastos de difícil justificación",
        help="Calculado como el 5% del rendimiento del periodo (ingresos - "
        "gastos reales).",
    )
    casilla_02 = fields.Monetary(
        string="Casilla [02] - Gastos", store=True, compute="_compute_casilla_02"
    )
    casilla_03 = fields.Monetary(
        string="Casilla [03] - Rendimiento",
        store=True,
        compute="_compute_casilla_03",
    )
    casilla_04 = fields.Monetary(
        string="Casilla [04] - IRPF",
        store=True,
        compute="_compute_casilla_04",
    )
    casilla_05 = fields.Monetary(string="Casilla [05]")
    casilla_06 = fields.Monetary(string="Casilla [06]")
    casilla_07 = fields.Monetary(
        string="Casilla [07]", store=True, compute="_compute_casilla_07"
    )
    casilla_08 = fields.Monetary(
        string="Casilla [08] - Ingresos primario",
        readonly=True,
    )
    casilla_09 = fields.Monetary(
        string="Casilla [09] - IRPF primario",
        readonly=True,
    )
    casilla_10 = fields.Monetary(string="Casilla [10]", readonly=True)
    casilla_11 = fields.Monetary(string="Casilla [11]", readonly=True)
    casilla_12 = fields.Monetary(
        string="Casilla [12]", store=True, compute="_compute_casilla_12"
    )
    casilla_13 = fields.Monetary(
        string="Casilla [13] - Deducción art. 80 bis",
        readonly=True,
    )
    casilla_14 = fields.Monetary(
        string="Casilla [14]", store=True, compute="_compute_casilla_14"
    )
    casilla_15 = fields.Monetary(string="Casilla [15]", readonly=True)
    casilla_16 = fields.Monetary(
        string="Casilla [16] - Deducción por pago de hipoteca",
        store=True,
        compute="_compute_casilla_16",
    )
    casilla_17 = fields.Monetary(
        string="Casilla [17]", store=True, compute="_compute_casilla_17"
    )
    casilla_18 = fields.Monetary(string="Casilla [18]", readonly=True)
    result = fields.Monetary(
        string="Resultado",
        compute="_compute_result",
        store=True,
    )
    tipo_declaracion = fields.Selection(
        selection=[("I", "A ingresar"), ("N", "Negativa"), ("B", "A deducir")],
        string="Tipo declaración",
        compute="_compute_tipo_declaracion",
        store=True,
    )

    @api.depends("real_expenses", "non_justified_expenses")
    def _compute_casilla_02(self):
        for report in self:
            report.casilla_02 = report.real_expenses + report.non_justified_expenses

    @api.depends("casilla_01", "casilla_02")
    def _compute_casilla_03(self):
        for report in self:
            report.casilla_03 = report.casilla_01 - report.casilla_02

    @api.depends("casilla_03")
    def _compute_casilla_04(self):
        for report in self:
            if report.casilla_03 < 0:
                report.casilla_04 = 0.0
            else:
                # IRPF - Truncar resultado, ya que es lo que hace la AEAT
                report.casilla_04 = trunc(0.20 * report.casilla_03, 2)

    @api.depends("casilla_04", "casilla_05", "casilla_06")
    def _compute_casilla_07(self):
        for report in self:
            report.casilla_07 = (
                report.casilla_04 - report.casilla_05 - report.casilla_06
            )

    @api.depends("casilla_07", "casilla_11", "activity_type")
    def _compute_casilla_12(self):
        for report in self:
            if report.activity_type == "other":
                report.casilla_12 = report.casilla_07 if report.casilla_07 > 0 else 0.0
            else:
                # TODO: Modelo 130 para actividades primarias
                report.casilla_12 = report.casilla_11

    @api.depends("casilla_12", "casilla_13")
    def _compute_casilla_14(self):
        for report in self:
            report.casilla_14 = report.casilla_12 - report.casilla_13

    @api.depends(
        "has_prestamo", "casilla_03", "casilla_14", "casilla_15", "activity_type"
    )
    def _compute_casilla_16(self):
        # Deducción por hipóteca
        self.casilla_16 = 0
        for report in self.filtered(lambda x: x.has_prestamo and x.casilla_14 > 0):
            # Truncar resultado, ya que es lo que hace la AEAT
            deduccion = trunc(0.02 * report.casilla_03, 2)
            if report.activity_type == "other":
                if deduccion > 660.14:
                    deduccion = 660.14
            else:
                raise exceptions.UserError(_("No implementado"))
            dif = report.casilla_14 - report.casilla_15
            if deduccion > dif:
                deduccion = dif
            report.casilla_16 = deduccion

    @api.depends("casilla_14", "casilla_15", "casilla_16")
    def _compute_casilla_17(self):
        for report in self:
            report.casilla_17 = (
                report.casilla_14 - report.casilla_15 - report.casilla_16
            )

    @api.depends("casilla_18", "casilla_17")
    def _compute_result(self):
        for report in self:
            report.result = report.casilla_17 - report.casilla_18

    @api.depends("result")
    def _compute_tipo_declaracion(self):
        for report in self:
            result = float_compare(report.result, 0, precision_digits=2)
            if result == 0:
                report.tipo_declaracion = "N"
            elif result < 0:
                report.tipo_declaracion = "B" if report.period_type != "4T" else "N"
            else:
                report.tipo_declaracion = "I"

    def _calc_ingresos_gastos_retenciones(self):
        self.ensure_one()
        aml_obj = self.env["account.move.line"]
        date_start = "%s-01-01" % self.year
        extra_domain = [
            ("company_id", "=", self.company_id.id),
            ("date", ">=", date_start),
            ("date", "<=", self.date_end),
        ]
        groups = aml_obj.read_group(
            [
                ("account_id.code", "=like", "7%"),
            ]
            + extra_domain,
            ["balance"],
            [],
        )
        incomes = groups[0]["balance"] and -groups[0]["balance"] or 0.0
        groups = aml_obj.read_group(
            [
                ("account_id.code", "=like", "6%"),
            ]
            + extra_domain,
            ["balance"],
            [],
        )
        expenses = groups[0]["balance"] or 0.0
        groups = aml_obj.read_group(
            [
                ("account_id.code", "=like", "473%"),
            ]
            + extra_domain,
            ["balance"],
            [],
        )
        withholdings = groups[0]["balance"] or 0.0
        return (incomes, expenses, withholdings)

    def _calc_prev_trimesters_data(self):
        self.ensure_one()
        amount = 0
        prev_reports = self._get_previous_fiscalyear_reports(self.date_start)
        for prev in prev_reports:
            if prev.casilla_07 > 0:
                amount += prev.casilla_07 - prev.casilla_16
        return amount

    def calculate(self):
        for report in self:
            if report.activity_type == "primary":
                raise exceptions.UserError(
                    _("Este tipo de actividad no está aún soportado por el módulo.")
                )
            if report.has_deduccion_80:
                raise exceptions.UserError(
                    _(
                        "No se pueden calcular por el momento declaraciones que "
                        "contengan deducciones por el artículo 80 bis."
                    )
                )
            vals = {
                "casilla_01": 0,
                "real_expenses": 0,
                "non_justified_expenses": 0,
                "casilla_05": 0,
                "casilla_06": 0,
                "casilla_13": 0,  # TODO: Deducción artículo 80 bis
                "casilla_15": 0,  # TODO: Poner resultados negativos ant. trimestres
            }
            if report.activity_type == "other":
                (
                    vals["casilla_01"],
                    vals["real_expenses"],
                    vals["casilla_06"],
                ) = report._calc_ingresos_gastos_retenciones()
                rendimiento_bruto = vals["casilla_01"] - vals["real_expenses"]
                if rendimiento_bruto > 0:
                    vals["non_justified_expenses"] = round(rendimiento_bruto * 0.05, 2)
                # Pago fraccionado previo del trimestre
                vals["casilla_05"] = report._calc_prev_trimesters_data()
            report.write(vals)
        return True

    def button_confirm(self):
        """Check its records"""
        msg = ""
        for report in self:
            if report.statement_type == "C" and not report.casilla_18:
                msg = _(
                    "Debe introducir una cantidad en la casilla 18 como "
                    "ha marcado la casilla de declaración complementaria."
                )
        if msg:
            raise exceptions.ValidationError(msg)
        return super().button_confirm()
