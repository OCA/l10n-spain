from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class L10nEsAeatMod180Report(models.Model):
    _description = "AEAT 180 report"
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod180.report"
    _aeat_number = "180"
    _period_yearly = True
    _period_quarterly = False
    _period_monthly = False

    casilla_01 = fields.Integer(
        string="[01] # Recipients",
        readonly=True,
        compute="_compute_casilla_01",
        help="Number of recipients",
    )
    casilla_02 = fields.Float(
        string="[02] Base retenciones e ingresos a cuenta",
        readonly=True,
        compute="_compute_casilla_02",
        store=True,
    )
    casilla_03 = fields.Float(
        string="[03] Retenciones e ingresos a cuenta",
        readonly=True,
        compute="_compute_casilla_03",
        help="Amount of retentions",
        store=True,
    )

    sign = fields.Selection(
        selection=[(" ", "Positivo"), ("N", "Negativo")],
        string="Signo Casilla 03",
        compute="_compute_casilla_03",
        store=True,
    )
    casilla_04 = fields.Float(
        string="[04] Fees to compensate",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Fee to compensate for prior results with same subject, "
        "fiscal year and period (in which his statement was to return "
        "and compensation back option was chosen).",
        store=True,
    )
    casilla_05 = fields.Float(
        string="[05] Result",
        readonly=True,
        compute="_compute_casilla_05",
        help="Result: ([03] - [04])",
        store=True,
    )
    tipo_declaracion = fields.Selection(
        selection=[
            ("I", "To enter"),
            ("U", "Direct debit"),
            ("G", "To enter on CCT"),
            ("N", "To return"),
        ],
        string="Result type",
        default="N",
        readonly=True,
        states={"draft": [("readonly", False)]},
        required=True,
    )
    tipo_declaracion_positiva = fields.Selection(
        selection=[("I", "To enter"), ("U", "Direct debit"), ("G", "To enter on CCT")],
        string="Result type (positive)",
        compute="_compute_tipo_declaracion",
        inverse="_inverse_tipo_declaracion",
        store=True,
    )
    tipo_declaracion_negativa = fields.Selection(
        selection=[("N", "To return")],
        string="Result type (negative)",
        compute="_compute_tipo_declaracion",
        inverse="_inverse_tipo_declaracion",
        store=True,
    )

    recipient_record_ids = fields.One2many(
        comodel_name="recipient.record",
        inverse_name="report_id",
        string="Registros de perceptores",
    )

    @api.depends("tipo_declaracion")
    def _compute_tipo_declaracion(self):
        for rec in self:
            if rec.tipo_declaracion == "N":
                rec.tipo_declaracion_negativa = rec.tipo_declaracion
                rec.tipo_declaracion_positiva = False
            else:
                rec.tipo_declaracion_positiva = rec.tipo_declaracion
                rec.tipo_declaracion_negativa = False

    def _inverse_tipo_declaracion(self):
        for rec in self:
            if rec.casilla_05 > 0.0:
                rec.tipo_declaracion = rec.tipo_declaracion_positiva
            else:
                rec.tipo_declaracion = rec.tipo_declaracion_negativa

    @api.constrains("tipo_declaracion")
    def _check_tipo_declaracion(self):
        for rec in self:
            if rec.casilla_05 <= 0.0 and rec.tipo_declaracion != "N":
                raise ValidationError(
                    _(
                        "The result of the declaration is negative. "
                        "You should select another Result type"
                    )
                )
            elif rec.casilla_05 > 0.0 and rec.tipo_declaracion == "N":
                raise ValidationError(
                    _(
                        "The result of the declaration is positive. "
                        "You should select another Result type"
                    )
                )

    @api.depends("tax_line_ids", "tax_line_ids.move_line_ids")
    def _compute_casilla_01(self):
        casillas = (2, 3)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas
            )
            report.casilla_01 = len(
                tax_lines.mapped("move_line_ids").mapped("partner_id")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_02(self):
        for report in self:
            tax_lines = report.tax_line_ids.filtered(lambda x: x.field_number == 2)
            report.casilla_02 = sum(tax_lines.mapped("amount"))

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_03(self):
        for report in self:
            tax_lines = report.tax_line_ids.filtered(lambda x: x.field_number == 3)
            report.casilla_03 = sum(tax_lines.mapped("amount"))
            if report.casilla_03 < 0:
                report.sign = "N"
            else:
                report.sign = " "

    @api.depends("casilla_03", "casilla_04")
    def _compute_casilla_05(self):
        for report in self:
            report.casilla_05 = report.casilla_03 - report.casilla_04

    def button_confirm(self):
        """Check bank account completion."""
        msg = ""
        for report in self.filtered(lambda x: not x.partner_bank_id):
            if report.tipo_declaracion in ("U", "N"):
                msg = (
                    _("Select an account for making the charge")
                    if report.tipo_declaracion == "U"
                    else _("Select an account for receiving the money")
                )
        if msg:
            raise UserError(msg)
        return super().button_confirm()

    def button_cancel(self):
        res = super().button_cancel()
        return res

    def button_recover(self):
        res = super().button_recover()
        return res

    def calculate(self):
        res = super().calculate()
        self._crear_registros_percetores()
        for rec in self:
            if rec.casilla_05 <= 0.0:
                rec.tipo_declaracion = "N"
            else:
                rec.tipo_declaracion = "I"
        return res

    def _crear_registros_percetores(self):
        self.recipient_record_ids.unlink()
        tax_code_map = self.env["l10n.es.aeat.map.tax"].search(
            [
                ("model", "=", self.number),
                "|",
                ("date_from", "<=", self.date_start),
                ("date_from", "=", False),
                "|",
                ("date_to", ">=", self.date_end),
                ("date_to", "=", False),
            ],
            limit=1,
        )
        if tax_code_map:
            report_taxes = self.get_taxes_from_templates(
                tax_code_map.map_line_ids.mapped("tax_ids")
            )
            if report_taxes:
                taxObj = self.env["account.tax"]
                perceptorObj = self.env["recipient.record"]
                unique_partner_ids = list(
                    set(
                        self.tax_line_ids.mapped("move_line_ids")
                        .mapped("partner_id")
                        .ids
                    )
                )
                unique_catastral_ids = list(
                    set(
                        self.tax_line_ids.mapped("move_line_ids")
                        .mapped("l10n_es_aeat_real_estate_id")
                        .ids
                    )
                )
                tax_ids = self.tax_line_ids.mapped("move_line_ids").mapped(
                    "tax_ids"
                ) + self.tax_line_ids.mapped("move_line_ids").mapped("tax_line_id")
                tax_ids = tax_ids.filtered(lambda at: at.id in report_taxes.ids)
                unique_tax_ids = list(set(tax_ids.ids))
                for partner_id in unique_partner_ids:
                    for catastral_id in unique_catastral_ids:
                        for tax_id in unique_tax_ids:
                            move_lines = self.tax_line_ids.mapped(
                                "move_line_ids"
                            ).filtered(
                                lambda aml: aml.partner_id.id == partner_id
                                and aml.l10n_es_aeat_real_estate_id.id == catastral_id
                            )
                            if move_lines:
                                base = sum(
                                    move_lines.filtered(
                                        lambda aml: tax_id in aml.tax_ids.ids
                                    ).mapped("debit")
                                ) - sum(
                                    move_lines.filtered(
                                        lambda aml: tax_id in aml.tax_ids.ids
                                    ).mapped("credit")
                                )

                                base_move_lines = move_lines.filtered(
                                    lambda aml: tax_id in aml.tax_ids.ids
                                )
                                # cuota_move_lines = move_lines.filtered(
                                #     lambda aml: tax_id == aml.tax_line_id.id
                                # )
                                cuota_percent = taxObj.browse(tax_id).amount
                                sign = " "
                                if base and base <= 0:
                                    sign = "N"
                                perceptorObj.create(
                                    {
                                        "report_id": self.id,
                                        "partner_id": partner_id,
                                        "l10n_es_aeat_real_estate_id": catastral_id,
                                        "sign": sign,
                                        "retentions_base": base,
                                        "retentions_fee": base
                                        * (cuota_percent / 100)
                                        * -1,
                                        "retentions_percentage": cuota_percent,
                                        "accrual_year": self.year,
                                        "base_move_line_ids": [
                                            [6, False, base_move_lines.ids]
                                        ],
                                    }
                                )

    @api.model
    def action_init_hook(self):
        mod115_ids = self.env["l10n.es.aeat.map.tax"].search([("model", "=", 115)])
        mod180_ids = self.env["l10n.es.aeat.map.tax"].search([("model", "=", 180)])
        # Eliminar mod180
        mod180_ids.mapped("map_line_ids").unlink()
        mod180_ids.unlink()
        # Duplicar mod115
        for mod115 in mod115_ids:
            new_180 = mod115.copy({"model": 180})
            for map_line in mod115.map_line_ids:
                map_line.copy({"map_parent_id": new_180.id})
        return True
