# 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class L10nEsAeatMod123Report(models.Model):
    _description = "AEAT 123 report"
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod123.report"
    _aeat_number = "123"

    number = fields.Char(default="123")
    casilla_01 = fields.Integer(
        string="[01] Número de perceptores",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Casilla [01] Número de perceptores",
    )
    casilla_02 = fields.Float(
        string="[02] Base retenciones",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Casilla [02] Base de la retención y/o del ingreso a cuenta",
    )
    casilla_03 = fields.Float(
        string="[03] Retenciones",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Casilla [03] Retenciones e ingresos a cuenta",
    )
    casilla_04 = fields.Float(
        string="[04] Ingresos ejercicios anteriores",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Casilla [04] Periodificación - Ingresos ejercicios anteriores",
    )
    casilla_05 = fields.Float(
        string="[05] Regularización",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Casilla [05] Periodificación - Regularización",
    )
    casilla_06 = fields.Float(
        string="[06] Total retenciones",
        readonly=True,
        compute="_compute_casilla06",
        help="Casilla [06] Suma de retenciones e ingresos a cuenta y "
        "regularización, en su caso ([3] + [5])",
    )
    casilla_07 = fields.Float(
        string="[07] Ingresos ejercicios anteriores",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Casilla [07] A deducir (exclusivamente en caso de declaración "
        "complementaria) Resultados a ingresar de anteriores "
        "declaraciones por el mismo concepto, ejercicio y período",
    )
    casilla_08 = fields.Float(
        string="[08] Resultado a ingresar", readonly=True, compute="_compute_casilla08"
    )
    casilla_01_2024 = fields.Integer(
        string="[01] Número de rentas. Dividendos y otras rentas de participación "
        "en fondos propios de entidades",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Casilla [01] Número de Rentas. Dividendos y otras rentas de participación "
        "en fondos propios de entidades. Totales de número de perceptores (se contará "
        "por números de NIF).",
    )
    casilla_02_2024 = fields.Integer(
        string="[02] Número de Rentas. Resto de rentas",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Número de rentas. Resto de rentas. Totales de número de perceptores "
        "(se contará por números de NIF).",
    )
    casilla_03_2024 = fields.Integer(
        string="[03] Número de Rentas. Totales",
        readonly=True,
        compute="_compute_casilla_03_2024",
        help="Casilla [03] ([01] + [02]). Número de Rentas. Totales.",
    )
    casilla_04_2024 = fields.Float(
        string="[04] Base de retenciones e ingresos a cuenta. Dividendos y otras rentas.",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Casilla [04] Base de retenciones e ingresos a cuenta. Dividendos y otras "
        "rentas de participación en fondos propios de entidades.",
    )
    casilla_05_2024 = fields.Float(
        string="[05] Base de retenciones e ingresos a cuenta. Resto de rentas",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Casilla [05] Base de retenciones e ingresos a cuenta. Resto de rentas.",
    )
    casilla_06_2024 = fields.Float(
        string="[06] Base de Retenciones e ingresos a cuenta. Totales",
        readonly=True,
        compute="_compute_casilla_06_2024",
        help="Casilla [06] ([05] + [06]). Base de retenciones e ingresos a cuenta.",
    )
    casilla_07_2024 = fields.Float(
        string="[07] Retenciones e ingresos a cuenta. Dividendos y otras rentas.",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Casilla [07] Retenciones e ingresos a cuenta. Dividendos y otras "
        "rentas de participación en fondos propios de entidades",
    )
    casilla_08_2024 = fields.Float(
        string="[08] Retenciones e ingresos a cuenta. Resto de rentas",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Casilla [08] Retenciones e ingresos a cuenta. Resto de rentas.",
    )
    casilla_09_2024 = fields.Float(
        string="[09] Retenciones e ingresos a cuenta. Totales",
        readonly=True,
        compute="_compute_casilla_09_2024",
        help="Casilla [09]([07] + [08]). Retenciones e ingresos a cuenta.",
    )
    casilla_10_2024 = fields.Float(
        string="[10] Ingresos ejercicios anteriores",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Casilla [10] Periodificación - Ingresos ejercicios anteriores",
    )
    casilla_11_2024 = fields.Float(
        string="[11] Regularización",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Casilla [11] Periodificación - Regularización",
    )
    casilla_12_2024 = fields.Float(
        string="[12] Total retenciones",
        readonly=True,
        compute="_compute_casilla_12_2024",
        help="Casilla [12] Suma de retenciones e ingresos a cuenta y "
        "regularización, en su caso ([9] + [11])",
    )
    casilla_13_2024 = fields.Float(
        string="[13] Ingresos ejercicios anteriores",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Casilla [13] A deducir (exclusivamente en caso de declaración "
        "complementaria) Resultados a ingresar de anteriores "
        "declaraciones por el mismo concepto, ejercicio y período",
    )
    casilla_14_2024 = fields.Float(
        string="[14] Resultado a ingresar",
        readonly=True,
        compute="_compute_casilla14_2024",
        help="Casilla [14] Resultado a ingresar ([12] - [13])",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moneda",
        readonly=True,
        related="company_id.currency_id",
        store=True,
    )
    tipo_declaracion = fields.Selection(
        selection=[
            ("I", "Ingreso"),
            ("U", "Domiciliación"),
            ("G", "Ingreso a anotar en CCT"),
            ("N", "Negativa"),
        ],
        string="Tipo de declaración",
        readonly=True,
        states={"draft": [("readonly", False)]},
        required=True,
    )
    amount_result = fields.Float(
        compute="_compute_amount_result", string="Resultado a ingresar"
    )

    @api.depends("casilla_03", "casilla_05")
    def _compute_casilla06(self):
        for report in self:
            report.casilla_06 = report.casilla_03 + report.casilla_05

    @api.depends("casilla_06", "casilla_07")
    def _compute_casilla08(self):
        for report in self:
            report.casilla_08 = report.casilla_06 + report.casilla_07

    @api.depends("casilla_01_2024", "casilla_02_2024")
    def _compute_casilla_03_2024(self):
        for report in self:
            report.casilla_03_2024 = report.casilla_01_2024 + report.casilla_02_2024

    @api.depends("casilla_04_2024", "casilla_05_2024")
    def _compute_casilla_06_2024(self):
        for report in self:
            report.casilla_06_2024 = report.casilla_04_2024 + report.casilla_05_2024

    @api.depends("casilla_07_2024", "casilla_08_2024")
    def _compute_casilla_09_2024(self):
        for report in self:
            report.casilla_09_2024 = report.casilla_07_2024 + report.casilla_08_2024

    @api.depends("casilla_09_2024", "casilla_11_2024")
    def _compute_casilla_12_2024(self):
        for report in self:
            report.casilla_12_2024 = report.casilla_09_2024 + report.casilla_11_2024

    @api.depends("casilla_12_2024", "casilla_13_2024")
    def _compute_casilla14_2024(self):
        for report in self:
            report.casilla_14_2024 = report.casilla_12_2024 - report.casilla_13_2024

    @api.depends("casilla_08", "casilla_14_2024", "year")
    def _compute_amount_result(self):
        for report in self:
            if report.year < 2024:
                report.amount_result = report.casilla_08
            else:
                report.amount_result = report.casilla_14_2024

    def calculate(self):
        pred = super().calculate()
        if self.year < 2024:
            move_lines02 = self.tax_line_ids.filtered(lambda r: r.field_number == 2)
            move_lines03 = self.tax_line_ids.filtered(lambda r: r.field_number == 3)
            self.casilla_02 = move_lines02.amount
            self.casilla_03 = move_lines03.amount
            partners = (move_lines02.move_line_ids + move_lines03.move_line_ids).mapped(
                "partner_id"
            )
            self.casilla_01 = len(set(partners.ids))
        else:
            field_numbers = [4, 5, 7, 8]
            tax_lines = {}
            for field_number in field_numbers:
                tax_lines[str(field_number)] = self.tax_line_ids.filtered(
                    lambda r: r.field_number == field_number
                )
                self["casilla_{:0>2}_2024".format(field_number)] = tax_lines[
                    str(field_number)
                ].amount
            self.casilla_01_2024 = len(
                (tax_lines["4"] + tax_lines["7"]).mapped("move_line_ids.partner_id")
            )
            self.casilla_02_2024 = len(
                (tax_lines["5"] + tax_lines["8"]).mapped("move_line_ids.partner_id")
            )
        return pred
