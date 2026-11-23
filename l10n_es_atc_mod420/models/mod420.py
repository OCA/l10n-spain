# Copyright 2023 Binhex - Nicolás Ramos
# Copyright 2024 Binhex - Christian Ramos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl

from odoo import api, exceptions, fields, models
from odoo.tools import float_compare

from odoo.addons.l10n_es_atc.models.l10n_es_atc_report import ATC_JAR_URL

# Counterpart of the result as in the AEAT model 303: Hacienda Pública
# acreedora (4750) for a result to enter, deudora (4700) for the rest
_ACCOUNT_PATTERN_MAP = {
    "C": "4700",
    "D": "4700",
    "N": "4700",
    "I": "4750",
}

ATC_JAR_URL["420"] = (
    "https://www3.gobiernodecanarias.org/tributos/atc/documents/d/agencia-tributaria-canaria/m420v930e26-zip-1"
)


class L10nEsAtcMod420Report(models.Model):
    _inherit = "l10n.es.atc.report"
    _name = "l10n.es.atc.mod420.report"
    _description = "ATC 420 Report"
    _aeat_number = "420"
    _period_quarterly = True
    _period_monthly = False
    _period_yearly = False

    total_devengado = fields.Monetary(
        string="[25] Total accrued installments",
        readonly=True,
        compute_sudo=True,
        compute="_compute_total_devengado",
        store=True,
    )

    # Cuotas devueltas en regimen de viajeros
    casilla_23 = fields.Monetary(
        string="[23] Traveler Base",
        default=0,
        help="Basis of the fee in the passenger regime made by the subject passive",
    )
    casilla_24 = fields.Monetary(
        string="[24] Traveler Fees",
        default=0,
        help="Fee in the passenger regime made by the taxpayer",
    )
    casilla_36 = fields.Monetary(
        string="[36] Livestock and fishing quotas",
        default=0,
        help="Quota of taxpayers covered by the special regime of the "
        "agriculture, Livestock and fishing",
    )
    casilla_37 = fields.Monetary(
        string="[37] Quotas Investment goods",
        default=0,
        help="Quota with positive or negative sign, of the regularization of the "
        "quotas supported by the acquisition or import of goods of "
        "investment",
    )
    casilla_38 = fields.Monetary(
        string="[38] Fee Before activity start",
        default=0,
        help="Quotas supported by the acquisition or importation of goods or "
        "services before the start of business activities or "
        "professionals",
    )
    casilla_39 = fields.Monetary(
        string="[39] Pro rata fee",
        default=0,
        help="Quotas for application of the final percentage of pro rata",
    )
    total_deducir = fields.Monetary(
        string="[40] Total deductible installments",
        readonly=True,
        compute_sudo=True,
        compute="_compute_total_deducir",
        store=True,
    )
    diferencia = fields.Monetary(
        string="[41] Difference",
        readonly=True,
        compute="_compute_diferencia",
        store=True,
        help="Difference between the amounts of boxes 25-40, either its "
        "import positive or negative",
    )
    regularizacion_cuotas = fields.Monetary(
        string="[42] Regularization of quotas",
        default=0,
        help="Amount corresponding to the quotas supported that could not "
        "be deducted and from which it is a debtor to the Treasury "
        "Public",
    )
    potential_cuotas_compensar = fields.Monetary(
        string="Pending quotas to compensate",
        default=0,
        help="Quotas in favor of the taxpayer from previous periods pending "
        "compensation. The calculation takes them from the previous "
        "declaration.",
    )
    cuotas_compensar = fields.Monetary(
        string="[43] quotas to compensate",
        default=0,
        help="The installments in favor of the taxpayer from previous periods "
        "pending compensation ",
    )
    remaining_cuotas_compensar = fields.Monetary(
        string="Remaining quotas to compensate",
        compute="_compute_remaining_cuotas_compensar",
    )
    a_deducir = fields.Monetary(
        string="[44] To deduct",
        default=0,
        help="This box will only be completed in the event of "
        "complementary self-assessment",
    )

    resultado_autoliquidacion = fields.Monetary(
        string="[45] Self-assessment result",
        readonly=True,
        compute="_compute_resultado_autoliquidacion",
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
        domain="[('company_ids', '=', company_id)]",
        store=True,
        readonly=False,
    )

    @api.depends("company_id", "result_type")
    def _compute_counterpart_account_id(self):
        for report in self:
            code = _ACCOUNT_PATTERN_MAP.get(report.result_type, "4750")
            report.counterpart_account_id = self.env["account.account"].search(
                [
                    ("code", "=like", f"{code}%"),
                    ("company_ids", "=", report.company_id.id),
                ],
                limit=1,
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount", "casilla_23", "casilla_24")
    def _compute_total_devengado(self):
        casillas_devengado = (3, 6, 9, 12, 15, 18, 20, 22)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas_devengado
            )
            report.total_devengado = sum(tax_lines.mapped("amount"))
            if not report.currency_id.is_zero(report.casilla_23):
                report.total_devengado -= report.casilla_24

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_total_deducir(self):
        casillas_deducir = (27, 29, 31, 33, 35, 36, 37, 38, 39)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas_deducir
            )
            report.total_deducir = sum(tax_lines.mapped("amount"))

    @api.depends("total_devengado", "total_deducir")
    def _compute_diferencia(self):
        for report in self:
            report.diferencia = report.total_devengado - report.total_deducir

    @api.depends("potential_cuotas_compensar", "cuotas_compensar")
    def _compute_remaining_cuotas_compensar(self):
        for report in self:
            report.remaining_cuotas_compensar = report.currency_id.round(
                report.potential_cuotas_compensar - report.cuotas_compensar
            )

    @api.depends("diferencia", "regularizacion_cuotas", "cuotas_compensar", "a_deducir")
    def _compute_resultado_autoliquidacion(self):
        for report in self:
            report.resultado_autoliquidacion = (
                report.diferencia
                + report.regularizacion_cuotas
                - report.cuotas_compensar
                - report.a_deducir
            )

    @api.constrains("statement_type")
    def _check_type(self):
        if "S" in self.mapped("statement_type"):
            raise exceptions.UserError(
                self.env._("You cannot make substitutive reports for this model.")
            )

    def _compute_allow_posting(self):
        for report in self:
            report.allow_posting = True

    @api.depends("resultado_autoliquidacion", "period_type")
    def _compute_result_type(self):
        for report in self:
            result = float_compare(
                report.resultado_autoliquidacion,
                0,
                precision_digits=report.currency_id.decimal_places,
            )
            if result == 0:
                report.result_type = "N"
            elif result == 1:
                report.result_type = "I"
            else:
                if report.period_type in ("4T", "12"):
                    report.result_type = "D"
                else:
                    report.result_type = "C"

    @api.onchange("statement_type")
    def onchange_type(self):
        if self.statement_type != "C":
            self.a_deducir = 0

    def calculate(self):
        """Compensate the quotas pending from the previous declaration, as
        the model 303 does."""
        self.cuotas_compensar = 0
        res = super().calculate()
        for report in self:
            prev_reports = self.search(
                [
                    ("company_id", "=", report.company_id.id),
                    ("date_start", "<", report.date_start),
                ]
            ).filtered(lambda m: m.state not in ["draft", "cancelled"])
            if prev_reports:
                prev_report = max(prev_reports, key=lambda x: x.date_end)
                if prev_report.remaining_cuotas_compensar >= 0:
                    amount = prev_report.remaining_cuotas_compensar
                    if prev_report.result_type == "C":
                        amount -= prev_report.resultado_autoliquidacion
                    report.potential_cuotas_compensar = max(0, amount)
            if report.period_type in ("4T", "12"):
                # The balance at the end of the year is returned, as with the
                # option to return in the last period of the model 303
                cuotas_compensar = report.potential_cuotas_compensar
            elif (
                float_compare(
                    report.resultado_autoliquidacion,
                    0,
                    precision_digits=report.currency_id.decimal_places,
                )
                != -1
            ):
                cuotas_compensar = min(
                    report.potential_cuotas_compensar,
                    report.resultado_autoliquidacion,
                )
            else:
                cuotas_compensar = 0
            report.cuotas_compensar = cuotas_compensar
        return res

    @api.constrains("potential_cuotas_compensar", "cuotas_compensar")
    def check_qty(self):
        if self.filtered(
            lambda x: (
                float_compare(
                    x.cuotas_compensar,
                    0,
                    precision_digits=x.currency_id.decimal_places,
                )
                < 0
                or float_compare(
                    x.remaining_cuotas_compensar,
                    0,
                    precision_digits=x.currency_id.decimal_places,
                )
                < 0
            )
        ):
            raise exceptions.ValidationError(
                self.env._(
                    "The quotas to compensate must be indicated as a positive "
                    "number, up to the pending ones."
                )
            )

    def _prepare_regularization_extra_move_lines(self):
        """The compensated quotas cancel the balance of Hacienda Pública
        deudora left by the previous declarations, as in the model 303."""
        lines = super()._prepare_regularization_extra_move_lines()
        if not (self.result_type == "I" and self.cuotas_compensar):
            return lines
        account = self.env["account.account"].search(
            [
                ("code", "=like", f"{_ACCOUNT_PATTERN_MAP['C']}%"),
                ("company_ids", "=", self.company_id.id),
            ],
            limit=1,
        )
        lines.append(
            {
                "name": self.env._("Compensation from previous periods"),
                "account_id": account.id,
                "partner_id": self.env.ref("l10n_es_atc.res_partner_atc").id,
                "debit": 0.0,
                "credit": self.cuotas_compensar,
            }
        )
        return lines

    @api.model
    def _prepare_counterpart_move_line(self, account, debit, credit):
        vals = super()._prepare_counterpart_move_line(account, debit, credit)
        vals.update(
            {
                "partner_id": self.env.ref("l10n_es_atc.res_partner_atc").id,
            }
        )
        return vals

    def button_confirm(self):
        if any(
            report.result_type == "D" and not report.partner_bank_id for report in self
        ):
            raise exceptions.UserError(
                self.env._("Select an account for receiving the money")
            )
        return super().button_confirm()

    def button_modelo_sobre(self):
        self.ensure_one()
        url = "/l10n_es_atc_mod420/static/src/pdf/caratula_sobre_420.pdf"
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "self",
        }

    def action_generar_mod420(self):
        self.ensure_one()
        self._atc_validate_fields()
        report_name = "l10n_es_atc_mod420.mod420_report_xml"
        # the jar filename to be used from .zip
        # downloaded from the url in ATC_JAR_URL
        jar_filename = "pa-mod420.jar"
        # the main class to be used from the jar file
        main_class = "org.grecasa.ext.pa.mod420.MIModelo420"
        # The filename of the report that the user will download
        filename = f"modelo{self._aeat_number}"
        # run the command and get the attachment
        attachment = self._atc_run_cmd(report_name, filename, jar_filename, main_class)
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
        }

    def _atc_get_messages(self):
        messages = super()._atc_get_messages()
        if not self.payment_type and self.resultado_autoliquidacion > 0:
            messages.append(self.env._("- Select a payment type"))
        if (
            self.output_type == "T"
            and self.payment_type
            and self.payment_type not in ["4", "5"]
        ):
            messages.append(
                self.env._(
                    "- The selected payment type "
                    "is not compatible with the output type. "
                    "Please select a different payment type."
                )
            )
        if self._is_partner_bank_required() and not self.partner_bank_id:
            messages.append(self.env._("- Select a bank account"))
        if not self.company_id.city_id.code:
            messages.append(
                self.env._(
                    "- Please set the code in the city: %s",
                    self.company_id.city_id.display_name,
                )
            )
        if not self.company_id.atc_public_way:
            messages.append(
                self.env._(
                    "- Please set the Public Way in the company",
                )
            )
        return messages

    def _is_partner_bank_required(self):
        return self.payment_type == "4" and self.result_type in ["I", "D"]
