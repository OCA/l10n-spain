# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2015-2019 Tecnativa - Pedro M. Baeza
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class L10nEsAeatMod216Report(models.Model):
    _description = "AEAT 216 report"
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod216.report"
    _aeat_number = "216"

    casilla_01_pre_2024 = fields.Integer(
        string="[01] # Recipients",
        readonly=True,
        compute="_compute_casilla_01_pre_2024",
        help="Income subject to retention - Number of recipients",
    )
    casilla_03_pre_2024 = fields.Monetary(
        string="[03] Amount of retentions",
        readonly=True,
        compute="_compute_casilla_03_pre_2024",
        help="Income subject to retention - Amount of retentions",
    )
    casilla_04_pre_2024 = fields.Integer(
        string="[04] # Recipients",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Income not subject to retention - Number of recipients",
    )
    casilla_05_pre_2024 = fields.Monetary(
        string="[05] Base amount",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Income not subject to retention - Base amount",
    )
    casilla_06_pre_2024 = fields.Monetary(
        string="[06] Fees to compensate",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Fee to compensate for prior results with same subject, "
        "fiscal year and period (in which his statement was to return "
        "and compensation back option was chosen).",
    )
    casilla_07_pre_2024 = fields.Monetary(
        string="[07] Result",
        readonly=True,
        compute="_compute_casilla_07_pre_2024",
        help="Result: ([03] - [06])",
    )
    casilla_05 = fields.Integer(
        string="[05] Número de rentas",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Deberá consignarse el número total de rentas sobre las que el declarante"
        " haya venido obligado a retener o a efectuar ingreso a cuenta en el mes o "
        "trimestre objeto de declaración.",
    )
    casilla_06 = fields.Integer(
        string="[06] Número de rentas",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Deberá consignarse el número total de rentas sobre las que el declarante"
        " haya venido obligado a retener o a efectuar ingreso a cuenta en el mes o "
        "trimestre objeto de declaración.",
    )
    casilla_07 = fields.Integer(
        string="[07] Número de rentas",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        compute="_compute_casilla_07",
        help="Deberá consignarse el número total de rentas sobre las que el declarante"
        " haya venido obligado a retener o a efectuar ingreso a cuenta declaradas en "
        "las casillas 05 y 06.",
    )
    casilla_08 = fields.Monetary(
        string="[08] Base de retenciones e ingresos a cuenta",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Se consignará la suma total de las bases de retención o de ingreso a "
        "cuenta correspondientes a las rentas declaradas en la casilla 05.",
    )
    casilla_09 = fields.Monetary(
        string="[09] Base de retenciones e ingresos a cuenta",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Se consignará la suma total de las bases de retención o de ingreso a "
        "cuenta correspondientes a las rentas declaradas en la casilla 06.",
    )
    casilla_10 = fields.Monetary(
        string="[10] Base de retenciones e ingresos a cuenta",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        compute="_compute_casilla_10",
        help="Se consignará la suma total de las bases de retención o de ingreso a "
        "cuenta declaradas en las casillas 08 y 09.",
    )
    casilla_11 = fields.Monetary(
        string="[11] Retenciones e ingresos a cuenta",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Se consignará el importe total de las retenciones e ingresos a cuenta "
        "que correspondan a las rentas declaradas en la casilla 05.",
    )
    casilla_12 = fields.Monetary(
        string="[12] Retenciones e ingresos a cuenta",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Se consignará el importe total de las retenciones e ingresos a cuenta "
        "que correspondan a las rentas declaradas en la casilla 06.",
    )
    casilla_13 = fields.Monetary(
        string="[13] Retenciones e ingresos a cuenta",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        compute="_compute_casilla_13",
        help="Se consignará el importe total de las retenciones e ingresos a cuenta "
        "declaradas en las casillas 11 y 12.",
    )
    casilla_14 = fields.Integer(
        string="[14] Número de rentas",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Deberá consignarse el número total de rentas sujetas al impuesto "
        "exceptuadas de retención o de ingreso a cuenta, conforme a lo previsto en los"
        " puntos 2 y 3 del artículo 2 de la Orden que aprueba este modelo (estos "
        "puntos se recogen en el apartado 'Obligados' de estas instrucciones como "
        "apartados Dos y Tres).",
    )
    casilla_15 = fields.Integer(
        string="[15] Número de rentas",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Deberá consignarse el número total de rentas sujetas al impuesto "
        "exceptuadas de retención o de ingreso a cuenta, conforme a lo previsto en los"
        " puntos 2 y 3 del artículo 2 de la Orden que aprueba este modelo (estos "
        "puntos se recogen en el apartado 'Obligados' de estas instrucciones como "
        "apartados Dos y Tres).",
    )
    casilla_16 = fields.Integer(
        string="[16] Número de rentas",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        compute="_compute_casilla_16",
        help="Deberá consignarse el número total de rentas sujetas al impuesto "
        "exceptuadas de retención o de ingreso a cuenta declaradas en las casillas 14 "
        "y 15.",
    )
    casilla_17 = fields.Monetary(
        string="[17] Base de retenciones e ingresos a cuenta",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Se consignará la suma total de las bases de retención o de ingreso a "
        "cuenta correspondientes a las rentas declaradas en la casilla 14.",
    )
    casilla_18 = fields.Monetary(
        string="[18] Base de retenciones e ingresos a cuenta",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Se consignará la suma total de las bases de retención o de ingreso a "
        "cuenta correspondientes a las rentas declaradas en la casilla 15.",
    )
    casilla_19 = fields.Monetary(
        string="[19] Base de retenciones e ingresos a cuenta",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        compute="_compute_casilla_19",
        help="Se consignará la suma total de las bases de retención o de ingreso a "
        "cuenta correspondientes a las rentas declaradas en las casillas 17 y 18.",
    )
    casilla_20 = fields.Monetary(
        string="[20] Resultados a ingresar de anteriores declaraciones por el mismo "
        "concepto, ejercicio y período",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Deberá consignarse en esta casilla el importe correspondiente a "
        "declaraciones anteriores, por el mismo concepto, ejercicio y período, "
        "exclusivamente en caso de declaración complementaria.",
    )
    casilla_21 = fields.Monetary(
        string="[21] Resultado a ingresar",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        compute="_compute_casilla_21",
        help="Deberá consignarse en esta casilla el importe correspondiente a la resta"
        " de las casillas 13 y 20",
    )
    tipo_declaracion = fields.Selection(
        selection=[
            ("I", "To enter"),
            ("U", "Direct debit"),
            ("G", "To enter on CCT"),
            ("N", "To return"),
        ],
        string="Result type",
        readonly=True,
        default="I",
        states={"draft": [("readonly", False)]},
        required=True,
    )

    @api.depends("tax_line_ids", "tax_line_ids.move_line_ids.partner_id")
    def _compute_casilla_01_pre_2024(self):
        casillas = (2, 3)
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas
            )
            report.casilla_01_pre_2024 = len(
                tax_lines.mapped("move_line_ids").mapped("partner_id")
            )

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_03_pre_2024(self):
        for report in self:
            tax_lines = report.tax_line_ids.filtered(lambda x: x.field_number == 3)
            report.casilla_03_pre_2024 = sum(tax_lines.mapped("amount"))

    @api.depends("casilla_03_pre_2024", "casilla_06_pre_2024")
    def _compute_casilla_07_pre_2024(self):
        for report in self:
            report.casilla_07_pre_2024 = (
                report.casilla_03_pre_2024 - report.casilla_06_pre_2024
            )

    @api.depends("casilla_05", "casilla_06")
    def _compute_casilla_07(self):
        for report in self:
            report.casilla_07 = report.casilla_05 + report.casilla_06

    @api.depends("casilla_08", "casilla_09")
    def _compute_casilla_10(self):
        for report in self:
            report.casilla_10 = report.casilla_08 + report.casilla_09

    @api.depends("casilla_11", "casilla_12")
    def _compute_casilla_13(self):
        for report in self:
            report.casilla_13 = report.casilla_11 + report.casilla_12

    @api.depends("casilla_14", "casilla_15")
    def _compute_casilla_16(self):
        for report in self:
            report.casilla_16 = report.casilla_14 + report.casilla_15

    @api.depends("casilla_17", "casilla_18")
    def _compute_casilla_19(self):
        for report in self:
            report.casilla_19 = report.casilla_17 + report.casilla_18

    @api.depends("casilla_13", "casilla_20")
    def _compute_casilla_21(self):
        for report in self:
            report.casilla_21 = report.casilla_13 - report.casilla_20

    def calculate(self):
        """Calculate the report."""
        res = super().calculate()
        for report in self.filtered_domain([("year", ">=", 2024)]):
            field_numbers = [9, 12]
            tax_lines = {}
            for field_number in field_numbers:
                tax_lines[str(field_number)] = report.tax_line_ids.filtered(
                    lambda r: r.field_number == field_number
                )
                report["casilla_{:0>2}".format(field_number)] = tax_lines[
                    str(field_number)
                ].amount
            report.casilla_06 = len(
                (tax_lines["9"] + tax_lines["12"])
                .mapped("move_line_ids")
                .mapped("partner_id")
            )
        return res
