# Copyright 2023 Binhex - Nicolás Ramos
# Copyright 2024 Binhex - Christian Ramos
# Copyright 2025 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl

from odoo import _, api, fields, models

from odoo.addons.l10n_es_atc.models.l10n_es_atc_report import ATC_JAR_URL

ATC_JAR_URL[
    "417"
] = "https://www3.gobiernodecanarias.org/tributos/atc/estatico/asistencia_contribuyente/modelos/ref_y_propios/igic/mod417/bin/M417V220E25.zip"


class L10nEsAtcmod417Report(models.Model):
    _inherit = "l10n.es.atc.report"
    _name = "l10n.es.atc.mod417.report"
    _description = "ATC 417 Report"
    _aeat_number = "417"
    _period_quarterly = False
    _period_monthly = True
    _period_yearly = False

    def _default_counterpart_417(self):
        return self.env["account.account"].search(
            [
                ("company_id", "=", self.env.company.id),
                ("code", "like", "4757%"),
            ]
        )[:1]

    company_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        related="company_id.partner_id",
        store=True,
    )
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
        help="Basis of the fee in the passenger regime made by the subject " "passive",
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
    cuotas_compensar = fields.Monetary(
        string="[43] quotas to compensate",
        default=0,
        help="The installments in favor of the taxpayer from previous periods "
        "pending compensation ",
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
            ("I", _("To enter")),
            ("D", _("To return")),
            ("C", _("To compensate")),
            ("N", _("No activity/Zero result")),
        ],
        string="Result type",
        compute="_compute_result_type",
    )
    bank_account_id = fields.Many2one(
        comodel_name="res.partner.bank",
        string="Bank account",
    )
    counterpart_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Counterpart account",
        default=_default_counterpart_417,
    )
    allow_posting = fields.Boolean(string="Allow posting", default=True)

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

    @api.depends("total_devengado")
    def _compute_resultado_autoliquidacion(self):
        for report in self:
            report.resultado_autoliquidacion = (
                report.diferencia
                + report.regularizacion_cuotas
                - report.cuotas_compensar
                - report.a_deducir
            )

    def _compute_allow_posting(self):
        self.allow_posting = True

    @api.depends("resultado_autoliquidacion", "period_type")
    def _compute_result_type(self):
        for report in self:
            if report.resultado_autoliquidacion == 0:
                report.result_type = "N"
            elif report.resultado_autoliquidacion > 0:
                report.result_type = "I"
            else:
                if report.period_type in ("4T", "12"):
                    report.result_type = "D"
                else:
                    report.result_type = "C"

    def button_confirm(self):
        """Check records"""
        msg = ""
        for mod417 in self:
            if mod417.result_type == "I" and not mod417.bank_account_id:
                msg = _("Select an account for making the charge")
            if mod417.result_type == "D" and not mod417.bank_account_id:
                msg = _("Select an account for receiving the money")
        if msg:
            # Don't raise error, because data is not used
            # raise exceptions.Warning(msg)
            pass
        return super().button_confirm()

    @api.model
    def _prepare_counterpart_move_line(self, account, debit, credit):
        vals = super()._prepare_counterpart_move_line(account, debit, credit)
        vals.update(
            {
                "partner_id": self.env.ref("l10n_es_atc.res_partner_atc").id,
            }
        )
        return vals

    def action_generar_mod417(self):
        self.ensure_one()
        self._atc_validate_fields()
        report_name = "l10n_es_atc_mod417.mod417_report_xml"
        # the jar filename to be used from .zip
        # downloaded from the url in ATC_JAR_URL
        jar_filename = "pa-mod417.jar"
        # the main class to be used from the jar file
        main_class = "org.grecasa.ext.pa.mod417.MIModelo417"
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
            messages.append(_("- Select a payment type"))
        if self.output_type == "T" and self.payment_type and self.payment_type != "5":
            messages.append(
                _(
                    "- The selected payment type "
                    "is not compatible with the output type. "
                    "Please select a different payment type."
                )
            )
        return messages
