# Copyright AvanzOSC - Ainara Galdona
# Copyright 2016 - Tecnativa - Antonio Espinosa
# Copyright 2016-2017 - Tecnativa - Pedro M. Baeza
# Copyright 2018 Valentin Vinagre <valentin.vinagre@qubiq.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class L10nEsAeatMod296Report(models.Model):

    _description = "AEAT 296 report"
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod296.report"
    _aeat_number = "296"

    casilla_01 = fields.Integer(
        string="[01] # Recipients",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="[01] Summary of the data included in the statement - "
        "Total number of perceivers",
    )
    casilla_02 = fields.Float(
        string="[02] Base retentions",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="[02] Summary of the data included in the statement - "
        "Base retention and income on account",
    )
    casilla_03 = fields.Float(
        string="[03] Retentions",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="[03] Summary of the data included in the statement - "
        "Retention and income on account",
    )
    casilla_04 = fields.Float(
        string="[04] Retentions entered",
        readonly=True,
        states={"calculated": [("readonly", False)]},
        help="[04] Summary of the data included in the statement - "
        "Retentions and income on account entered",
    )
    lines296 = fields.One2many(
        comodel_name="l10n.es.aeat.mod296.report.line",
        inverse_name="mod296_id",
        string="Lines",
    )

    def partner_group(self, move_lines_base_ids, move_lines_cuota_ids):
        partner_groups = {}
        for group in self.env["account.move.line"].read_group(
            [("id", "in", move_lines_base_ids)],
            ["partner_id", "credit", "debit"],
            ["partner_id"],
        ):
            partner_groups[group["partner_id"][0]] = {
                "base": {"credit": group["credit"], "debit": group["debit"]}
            }
        for group in self.env["account.move.line"].read_group(
            [("id", "in", move_lines_cuota_ids)],
            ["partner_id", "credit", "debit"],
            ["partner_id"],
        ):
            partner_groups[group["partner_id"][0]]["cuota"] = {
                "credit": group["credit"],
                "debit": group["debit"],
            }
        return partner_groups

    def calculate(self):
        res = super().calculate()
        for report in self:
            report.lines296.unlink()
            line_lst = []
            tax_lines_number_2 = report.tax_line_ids.filtered(
                lambda x: x.field_number == 2
            )
            tax_lines_number_3 = report.tax_line_ids.filtered(
                lambda x: x.field_number == 3
            )
            move_lines_base = tax_lines_number_2.mapped("move_line_ids")
            move_lines_cuota = tax_lines_number_3.mapped("move_line_ids")
            partner_groups = self.partner_group(
                move_lines_base.ids, move_lines_cuota.ids
            )
            for partner_id in partner_groups:
                move_lines_base_partner = move_lines_base.filtered(
                    lambda x: x.partner_id.id == partner_id
                )
                move_lines_cuota_partner = move_lines_cuota.filtered(
                    lambda x: x.partner_id.id == partner_id
                )
                data = self._prepare_mod296_line(
                    partner_id,
                    partner_groups[partner_id],
                    (move_lines_base_partner + move_lines_cuota_partner),
                )
                line_lst.append((0, 0, data))
            report.lines296 = line_lst
            report.lines296.onchange_partner()
            report.casilla_01 = len(partner_groups)
            report.casilla_02 = sum(tax_lines_number_2.mapped("amount"))
            report.casilla_03 = sum(tax_lines_number_3.mapped("amount"))
        return res

    def _prepare_mod296_line(self, partner_id, data, move_lines):
        return {
            "partner_id": partner_id,
            "move_line_ids": move_lines,
            "base_retenciones_ingresos": data["base"]["debit"] - data["base"]["credit"],
            "retenciones_ingresos": data["cuota"]["credit"] - data["cuota"]["debit"],
        }


class L10nEsAeatMod296ReportLine(models.Model):
    _description = "AEAT 296 report line"
    _name = "l10n.es.aeat.mod296.report.line"

    mod296_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod296.report", string="Mod 296"
    )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner")
    move_line_ids = fields.Many2many(
        comodel_name="account.move.line", string="Move Lines"
    )
    base_retenciones_ingresos = fields.Float(
        string="Base retention and " "income on account"
    )
    porcentaje_retencion = fields.Float(string="% retention")
    retenciones_ingresos = fields.Float(string="Retention and income on " "account")
    fisica_juridica = fields.Selection(
        selection=[("F", "Physical person"), ("J", "Legal person or entity")],
        string="F/J",
    )
    naturaleza = fields.Selection(
        selection=[("D", "Money income"), ("E", "Income in kind")], string="Nature"
    )
    fecha_devengo = fields.Date(string="Devengo date")
    clave = fields.Selection(
        selection=[
            (
                "1",
                "1 - Dividends and other income derived from the participation "
                "in own funds of entities.",
            ),
            (
                "2",
                "2 - Interest and other income derived from the transfer to "
                "parties of own capital.",
            ),
            (
                "3",
                "3 - Canons derived from patents, trademarks, drawings or "
                "models, plans, formulas or secret procedures.",
            ),
            ("4", "4 - Fees derived from rights on literary and artistic works."),
            ("5", "5 - Canons derived from rights on scientific works."),
            (
                "6",
                "6 - Fees derived from rights on cinematographic films "
                "and recorded sound or visual works.",
            ),
            (
                "7",
                "7 - Canons derived from information related to industrial, "
                "commercial or scientific experiences (know-how).",
            ),
            ("8", "8 - Fees derived from rights on computer programs."),
            (
                "9",
                "9 - Fees derived from personal rights susceptible to "
                "transfer, such as image rights.",
            ),
            (
                "10",
                "10 - Canons derived from industrial, commercial or "
                "scientific equipment.",
            ),
            ("11", "11 - Other canons not previously mentioned."),
            (
                "12",
                "12 - Capital income from capitalization operations and "
                "life or disability insurance contracts.",
            ),
            ("13", "13 - Other income from movable capital not mentioned above."),
            ("14", "14 - Real estate performance."),
            ("15", "15 - Performance of business activities."),
            ("16", "16 - Rents derived from technical assistance benefits."),
            ("17", "17 - Rents of artistic activities."),
            ("18", "18 - Rents of sports activities."),
            ("19", "19 - Rents of professional activities."),
            ("20", "20 - Rents of work."),
            ("21", "21 - Pensions and passive assets."),
            (
                "22",
                "22 - Remuneration of administrators and members of boards of "
                "directors.",
            ),
            ("23", "23 - Performance derived from reinsurance operations."),
            ("24", "24 - Maritime or air navigation entities."),
            ("25", "25 - Other rents"),
        ],
        string="Key",
    )
    subclave = fields.Selection(
        selection=[
            (
                "1",
                "1 - Retention practiced at the general rates or scales of "
                "taxation of article 25 of the rewritten text of the "
                "Non-Resident Income Tax Law.",
            ),
            (
                "2",
                "2 - Retention practiced applying limits of imposition of "
                "Agreements.",
            ),
            (
                "3",
                "3 - Internal exemption (mainly: article 14 of the revised "
                "text of the Law on Non-Resident Income Tax)",
            ),
            ("4", "4 - Exemption by application of a Convention."),
            (
                "5",
                "5 - No Retention for previous payment of the Tax by "
                "the taxpayer or his representative..",
            ),
            (
                "6",
                "6 - The declared recipient is a foreign entity "
                "for the collective management of intellectual property rights, "
                "with a retention having applied the limit of taxation, or "
                "the exemption, of a Convention.",
            ),
            (
                "7",
                "7 - The recipient is a taxpayer of the Personal Income Tax of "
                "the special regime applicable to workers displaced "
                "to Spanish territory.",
            ),
            (
                "8",
                "8 - The declared recipient is an entity resident abroad that "
                "sells shares or units of Spanish collective investment "
                "institutions, with a withholding tax applying a limit "
                "of taxation established in the lower Agreement.",
            ),
            (
                "9",
                "9 - The declared recipient is an entity residing abroad "
                "selling shares or participations of Spanish collective investment"
                " institutions, with a retention having applied the type of lien.",
            ),
        ],
        string="Subkey",
    )
    mediador = fields.Boolean(string="Mediator")
    codigo = fields.Selection(
        selection=[
            ("1", "1. Emisor code corresponds to an N.I.F."),
            ("2", "2. Emisor code corresponds to an code I.S.I.N."),
            (
                "3",
                "3. Emisor code corresponds to values foreign that have not "
                "been assigned I.S.I.N., whose emisor does not have a NIF",
            ),
        ],
        string="Code",
    )
    codigo_emisor = fields.Char(string="Emisor code", size=12)
    pago = fields.Selection(
        selection=[("1", "As transmitter"), ("2", "As mediator")], string="Payment"
    )
    tipo_codigo = fields.Selection(
        selection=[
            ("C", "Identification with the Account " "Code Values (C.C.V.)"),
            ("O", "Other identification"),
        ],
        string="Code type",
    )
    cuenta_valores = fields.Many2one(
        comodel_name="res.partner.bank", string="Code Account Values"
    )
    pendiente = fields.Boolean(string="Pending")
    domicilio = fields.Char(string="Domicile", size=50)
    complemento_domicilio = fields.Char(string="Domicile Complement", size=40)
    poblacion = fields.Char(string="Population/City", size=30)
    provincia = fields.Many2one(
        comodel_name="res.country.state", string="Province/Region/State"
    )
    zip = fields.Char(string="Postal Code", size=10)
    pais = fields.Many2one(comodel_name="res.country", string="Country")
    nif_pais_residencia = fields.Char(string="Nif in the country of residence", size=20)
    fecha_nacimiento = fields.Date(string="Date of birth")
    ciudad_nacimiento = fields.Char(string="Birth city", size=35)
    pais_nacimiento = fields.Many2one(
        comodel_name="res.country", string="Country of birth"
    )
    pais_residencia_fiscal = fields.Many2one(
        comodel_name="res.country", string="Country territory of fiscal residence"
    )
    fecha_devengo_export = fields.Char(
        string="Devengo date export", compute="_compute_get_fecha_devengo_export"
    )
    fecha_nacimiento_export = fields.Char(
        string="Date of birth export", compute="_compute_get_fecha_nacimiento_export"
    )

    @api.depends("fecha_devengo")
    def _compute_get_fecha_devengo_export(self):
        for sel in self:
            res = ""
            if sel.fecha_devengo:
                res = fields.Date.to_date(sel.fecha_devengo).strftime("%d%m%Y")
            sel.fecha_devengo_export = res

    @api.depends("fecha_nacimiento")
    def _compute_get_fecha_nacimiento_export(self):
        for sel in self:
            res = ""
            if sel.fecha_nacimiento:
                res = fields.Date.to_date(sel.fecha_nacimiento).strftime("%d%m%Y")
            sel.fecha_nacimiento_export = res

    @api.onchange("partner_id")
    def onchange_partner(self):
        for sel in self.filtered(lambda x: x.partner_id):
            sel.write(
                {
                    "domicilio": sel.partner_id.street,
                    "complemento_domicilio": sel.partner_id.street2,
                    "poblacion": sel.partner_id.city,
                    "provincia": sel.partner_id.state_id,
                    "zip": sel.partner_id.zip,
                    "pais": sel.partner_id.country_id,
                }
            )
