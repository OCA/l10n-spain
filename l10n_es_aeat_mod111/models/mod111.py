# Copyright 2015 Ainara Galdona (http://www.avanzosc.es)
# Copyright 2016 RGB Consulting SL (http://www.rgbconsulting.com)
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016 Vicent Cubells (http://obertix.net)
# Copyright 2016 Jose Maria Alzaga (http://www.aselcis.com)
# Copyright 2016 Ismael Calvo (http://factorlibre.com)
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2022 Jairo Llopis <jairo@moduon.team>
# Copyright 2022 Eduardo de Miguel <edu@moduon.team>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl

from odoo import api, fields, models


class L10nEsAeatMod111Report(models.Model):

    _description = "AEAT 111 report"
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod111.report"
    _aeat_number = "111"

    casilla_01 = fields.Integer(
        string="[01] # Recipients",
        compute_sudo=True,
        compute="_compute_casilla_01",
        store=True,
        readonly=False,
        help="Work income - Monetary - Number of recipients",
    )
    casilla_02 = fields.Monetary(
        string="[02] Taxable",
        readonly=True,
        compute_sudo=True,
        compute="_compute_casilla_02",
        store=True,
        help="Work income - In kind - Base taxable value",
    )
    casilla_03 = fields.Monetary(
        string="[03] Amount retained",
        readonly=True,
        compute_sudo=True,
        compute="_compute_casilla_03",
        store=True,
        help="Work income - In kind - Amount retained",
    )
    casilla_04 = fields.Integer(
        string="[04] # Recipients",
        compute_sudo=True,
        compute="_compute_casilla_04",
        store=True,
        readonly=False,
        help="Work income - In kind - Number of recipients",
    )
    casilla_05 = fields.Monetary(
        string="[05] Taxable",
        readonly=True,
        compute_sudo=True,
        compute="_compute_casilla_05",
        store=True,
        help="Work income - In kind - Base taxable value",
    )
    casilla_06 = fields.Monetary(
        string="[06] Amount retained",
        readonly=True,
        compute_sudo=True,
        compute="_compute_casilla_06",
        store=True,
        help="Work income - In kind - Amount retained",
    )
    casilla_07 = fields.Integer(
        string="[07] # Recipients",
        compute_sudo=True,
        compute="_compute_casilla_07",
        store=True,
        readonly=False,
        help="Business income - Monetary - Number of recipients",
    )
    casilla_08 = fields.Monetary(
        string="[08] Taxable",
        readonly=True,
        compute_sudo=True,
        compute="_compute_casilla_08",
        store=True,
        help="Business income - In kind - Base taxable value",
    )
    casilla_09 = fields.Monetary(
        string="[09] Amount retained",
        readonly=True,
        compute_sudo=True,
        compute="_compute_casilla_09",
        store=True,
        help="Business income - In kind - Amount retained",
    )
    casilla_10 = fields.Integer(
        string="[10] # Recipients",
        compute_sudo=True,
        compute="_compute_casilla_10",
        store=True,
        readonly=False,
        help="Business income - In kind - Number of recipients",
    )
    casilla_11 = fields.Monetary(
        string="[11] Taxable",
        readonly=True,
        compute_sudo=True,
        compute="_compute_casilla_11",
        store=True,
        help="Business income - In kind - Base taxable value",
    )
    casilla_12 = fields.Monetary(
        string="[12] Amount retained",
        readonly=True,
        compute_sudo=True,
        compute="_compute_casilla_12",
        store=True,
        help="Business income - In kind - Amount retained",
    )
    casilla_13 = fields.Integer(
        string="[13] # Recipients",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Awards for participation in games, contests, raffles or "
        "random combinations - Monetary - Number of recipients",
    )
    casilla_14 = fields.Monetary(
        string="[14] Taxable",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Awards for participation in games, contests, raffles or "
        "random combinations - Monetary - Base taxable value",
    )
    casilla_15 = fields.Monetary(
        string="[15] Amount retained",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Awards for participation in games, contests, raffles or "
        "random combinations - Monetary - Amount retained",
    )
    casilla_16 = fields.Integer(
        string="[16] # Recipients",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Awards for participation in games, contests, raffles or "
        "random combinations - In kind - Number of recipients",
    )
    casilla_17 = fields.Monetary(
        string="[17] Taxable",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Awards for participation in games, contests, raffles or "
        "random combinations - In kind - Base taxable value",
    )
    casilla_18 = fields.Monetary(
        string="[18] Amount retained",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Awards for participation in games, contests, raffles or "
        "random combinations - In kind - Amount retained",
    )
    casilla_19 = fields.Integer(
        string="[19] # Recipients",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Capital gains derived from the forest exploitation of "
        "residents in public forests - Monetary - Number of recipients",
    )
    casilla_20 = fields.Monetary(
        string="[20] Taxable",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Capital gains derived from the forest exploitation of "
        "residents in public forests - Monetary - Base taxable value",
    )
    casilla_21 = fields.Monetary(
        string="[21] Amount retained",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Capital gains derived from the forest exploitation of "
        "residents in public forests - Monetary - Amount retained",
    )
    casilla_22 = fields.Integer(
        string="[22] # Recipients",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Capital gains derived from the forest exploitation of "
        "residents in public forests - In kind - Number of recipients",
    )
    casilla_23 = fields.Monetary(
        string="[23] Taxable",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Capital gains derived from the forest exploitation of "
        "residents in public forests - In kind - Base taxable value",
    )
    casilla_24 = fields.Monetary(
        string="[24] Amount retained",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Capital gains derived from the forest exploitation of "
        "residents in public forests - In kind - Amount retained",
    )
    casilla_25 = fields.Integer(
        string="[25] # Recipients",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Consideration for the transfer of image rights: income "
        "account provided in Article 92.8 of the Tax Law - "
        "Monetary or in kind - Number of recipients",
    )
    casilla_26 = fields.Monetary(
        string="[26] Taxable",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Consideration for the transfer of image rights: income "
        "account provided in Article 92.8 of the Tax Law - "
        "Monetary or in kind - Base taxable value",
    )
    casilla_27 = fields.Monetary(
        string="[27] Amount retained",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Consideration for the transfer of image rights: income "
        "account provided in Article 92.8 of the Tax Law - "
        "Monetary or in kind - Amount retained",
    )
    casilla_28 = fields.Monetary(
        string="[28] Amount of retentions",
        compute_sudo=True,
        readonly=True,
        compute="_compute_casilla_28",
        help="Amount of retentions: "
        "([03] + [06] + [09] + [12] + [15] + [18] + [21] + [24] + [27])",
    )
    casilla_29 = fields.Monetary(
        string="[29] Fees to compensate",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="Fee to compensate for prior results with same subject, "
        "fiscal year and period (in which his statement was to return "
        "and compensation back option was chosen).",
    )
    casilla_30 = fields.Monetary(
        string="[30] Result",
        readonly=True,
        compute="_compute_casilla_30",
        help="Result: ([28] - [29])",
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
    colegio_concertado = fields.Boolean(
        string="College concerted",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=False,
    )

    @api.depends("tax_line_ids", "tax_line_ids.move_line_ids.partner_id")
    def _compute_casilla_01(self):
        casillas = {2, 3}
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas
            )
            report.casilla_01 = len(tax_lines.mapped("move_line_ids.partner_id"))

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

    @api.depends("tax_line_ids", "tax_line_ids.move_line_ids.partner_id")
    def _compute_casilla_04(self):
        casillas = {5, 6}
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas
            )
            report.casilla_04 = len(tax_lines.mapped("move_line_ids.partner_id"))

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_05(self):
        for report in self:
            tax_lines = report.tax_line_ids.filtered(lambda x: x.field_number == 5)
            report.casilla_05 = sum(tax_lines.mapped("amount"))

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_06(self):
        for report in self:
            tax_lines = report.tax_line_ids.filtered(lambda x: x.field_number == 6)
            report.casilla_06 = sum(tax_lines.mapped("amount"))

    @api.depends("tax_line_ids", "tax_line_ids.move_line_ids.partner_id")
    def _compute_casilla_07(self):
        casillas = {8, 9}
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas
            )
            report.casilla_07 = len(tax_lines.mapped("move_line_ids.partner_id"))

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_08(self):
        for report in self:
            tax_lines = report.tax_line_ids.filtered(lambda x: x.field_number == 8)
            report.casilla_08 = sum(tax_lines.mapped("amount"))

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_09(self):
        for report in self:
            tax_lines = report.tax_line_ids.filtered(lambda x: x.field_number == 9)
            report.casilla_09 = sum(tax_lines.mapped("amount"))

    @api.depends("tax_line_ids", "tax_line_ids.move_line_ids.partner_id")
    def _compute_casilla_10(self):
        casillas = {11, 12}
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.field_number in casillas
            )
            report.casilla_10 = len(tax_lines.mapped("move_line_ids.partner_id"))

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_11(self):
        for report in self:
            tax_lines = report.tax_line_ids.filtered(lambda x: x.field_number == 11)
            report.casilla_11 = sum(tax_lines.mapped("amount"))

    @api.depends("tax_line_ids", "tax_line_ids.amount")
    def _compute_casilla_12(self):
        for report in self:
            tax_lines = report.tax_line_ids.filtered(lambda x: x.field_number == 12)
            report.casilla_12 = sum(tax_lines.mapped("amount"))

    @api.depends(
        "casilla_03",
        "casilla_06",
        "casilla_09",
        "casilla_12",
        "casilla_15",
        "casilla_18",
        "casilla_21",
        "casilla_24",
        "casilla_27",
    )
    def _compute_casilla_28(self):
        for report in self:
            report.casilla_28 = (
                report.casilla_03
                + report.casilla_06
                + report.casilla_09
                + report.casilla_12
                + report.casilla_15
                + report.casilla_18
                + report.casilla_21
                + report.casilla_24
                + report.casilla_27
            )

    @api.depends("casilla_28", "casilla_29")
    def _compute_casilla_30(self):
        for report in self:
            report.casilla_30 = report.casilla_28 - report.casilla_29
