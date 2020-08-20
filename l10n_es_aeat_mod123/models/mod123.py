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

    @api.depends("casilla_03", "casilla_05")
    def _compute_casilla06(self):
        for report in self:
            report.casilla_06 = report.casilla_03 + report.casilla_05

    @api.depends("casilla_06", "casilla_07")
    def _compute_casilla08(self):
        for report in self:
            report.casilla_08 = report.casilla_06 + report.casilla_07

    def calculate(self):
        super(L10nEsAeatMod123Report, self).calculate()
        move_lines02 = self.tax_line_ids.filtered(lambda r: r.field_number == 2)
        move_lines03 = self.tax_line_ids.filtered(lambda r: r.field_number == 3)
        self.casilla_02 = move_lines02.amount
        self.casilla_03 = move_lines03.amount
        partners = (move_lines02.move_line_ids + move_lines03.move_line_ids).mapped(
            "partner_id"
        )
        self.casilla_01 = len(set(partners.ids))
