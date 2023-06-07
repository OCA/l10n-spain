##############################################################################
#
# Copyright (c) 2023 Binhex System Solutions
# Copyright (c) 2023 Nicolás Ramos (http://binhex.es)
#
# The licence is in the file __manifest__.py
##############################################################################


from odoo import models, fields, api, _


class L10nEsAtcMod420Report(models.Model):
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.atc.mod420.report"
    _description = "ATC 420 Report"
    _aeat_number = "420"
    _period_quarterly = True
    _period_monthly = False
    _period_yearly = False

    def _default_counterpart_420(self):
        return self.env["account.account"].search(
            [
                ("code", "like", "4757%"),
            ]
        )[:1]

    company_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string=_("Partner"),
        related="company_id.partner_id",
        store=True,
    )
    total_devengado = fields.Float(
        string=_("[25] Total accrued installments"),
        readonly=True,
        compute_sudo=True,
        compute="_compute_total_devengado",
        store=True,
    )

    # Cuotas devueltas en regimen de viajeros
    casilla_23 = fields.Float(
        string=_("[23] Traveler Base"),
        default=0,
        states={"done": [("readonly", True)]},
        help=_(
            "Basis of the fee in the passenger regime made by the subject "
            "passive"
        ),
    )
    casilla_24 = fields.Float(
        string=_("[24] Traveler Fees"),
        default=0,
        states={"done": [("readonly", True)]},
        help=_("Fee in the passenger regime made by the taxpayer"),
    )
    casilla_36 = fields.Float(
        string=_("[36] Livestock and fishing quotas"),
        default=0,
        states={"done": [("readonly", True)]},
        help=_(
            "Quota of taxpayers covered by the special regime of the "
            "agriculture, Livestock and fishing"
        ),
    )
    casilla_37 = fields.Float(
        string=_("[37] Quotas Investment goods"),
        default=0,
        states={"done": [("readonly", True)]},
        help=_(
            "Quota with positive or negative sign, of the regularization of the "
            "quotas supported by the acquisition or import of goods of "
            "investment"
        ),
    )
    casilla_38 = fields.Float(
        string=_("[38] Fee Before activity start"),
        default=0,
        states={"done": [("readonly", True)]},
        help=_(
            "Quotas supported by the acquisition or importation of goods or "
            "services before the start of business activities or "
            "professionals"
        ),
    )
    casilla_39 = fields.Float(
        string=_("[39] Pro rata fee"),
        default=0,
        states={"done": [("readonly", True)]},
        help=_("Quotas for application of the final percentage of pro rata"),
    )
    total_deducir = fields.Float(
        string=_("[40] Total deductible installments"),
        readonly=True,
        compute_sudo=True,
        compute="_compute_total_deducir",
        store=True,
    )
    diferencia = fields.Float(
        string=_("[41] Difference"),
        readonly=True,
        compute="_compute_diferencia",
        store=True,
        help=_(
            "Difference between the amounts of boxes 25-40, either its "
            "import positive or negative"
        ),
    )
    regularizacion_cuotas = fields.Float(
        string=_("[42] Regularization of quotas"),
        default=0,
        states={"done": [("readonly", True)]},
        help=_(
            "Amount corresponding to the quotas supported that could not "
            "be deducted and from which it is a debtor to the Treasury "
            "Public"
        ),
    )
    cuotas_compensar = fields.Float(
        string=_("[43] quotas to compensate"),
        default=0,
        states={"done": [("readonly", True)]},
        help=_(
            "The installments in favor of the taxpayer from previous periods "
            "pending compensation "
        ),
    )
    a_deducir = fields.Float(
        string=_("[44] To deduct"),
        default=0,
        states={"done": [("readonly", True)]},
        help=_(
            "This box will only be completed in the event of "
            "complementary self-assessment"
        ),
    )

    resultado_autoliquidacion = fields.Float(
        string=_("[45] Self-assessment result"),
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
        string=_("Result type"),
        compute="_compute_result_type",
    )
    bank_account_id = fields.Many2one(
        comodel_name="res.partner.bank",
        string=_("Bank account"),
        states={"done": [("readonly", True)]},
    )
    counterpart_account_id = fields.Many2one(
        comodel_name="account.account",
        string=_("Counterpart account"),
        default=_default_counterpart_420,
    )
    allow_posting = fields.Boolean(string=_("Allow posting"), default=True)

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_total_devengado(self):
        casillas_devengado = (3, 6, 9, 12, 15, 18, 20, 22, 24)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas_devengado
            )
            report.total_devengado = sum(tax_lines.mapped("amount"))

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
        for report in self:
            report.allow_posting = True

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
        for mod420 in self:
            if mod420.result_type == "I" and not mod420.bank_account_id:
                msg = _("Select an account for making the charge")
            if mod420.result_type == "D" and not mod420.bank_account_id:
                msg = _("Select an account for receiving the money")
        if msg:
            # Don't raise error, because data is not used
            # raise exceptions.Warning(msg)
            pass
        return super(L10nEsAtcMod420Report, self).button_confirm()

    def button_modelo_sobre(self):
        self.ensure_one()
        url = str("/l10n_es_atc_mod420/static/src/pdf/caratula_sobre_420.pdf")
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "self",
            "tag": "reload",
        }
