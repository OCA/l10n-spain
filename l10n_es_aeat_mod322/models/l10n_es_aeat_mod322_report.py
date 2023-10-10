# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

from odoo.addons.l10n_es_aeat_mod303.models.mod303 import (
    ACTIVITY_CODE_DOMAIN,
    EDITABLE_ON_DRAFT,
    NON_EDITABLE_ON_DONE,
)


class L10nEsAeatMod322Report(models.Model):
    _name = "l10n.es.aeat.mod322.report"
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _description = "AEAT 322 Report"
    _period_quarterly = False
    _aeat_number = "322"

    vinculated_partner_ids = fields.Many2many(
        "res.partner",
        states=EDITABLE_ON_DRAFT,
        store=True,
        compute="_compute_company_info",
    )
    company_type = fields.Selection(
        string="Tipo de compañía",
        selection=[
            ("D", "Dominante"),
            ("P", "Dependiente"),
        ],
        compute="_compute_company_info",
        states=EDITABLE_ON_DRAFT,
        store=True,
    )
    dominant_company_vat = fields.Char(
        string="NIF de la entidad dominante",
        compute="_compute_company_info",
        store=True,
        states=EDITABLE_ON_DRAFT,
    )
    group_number = fields.Char(
        string="Nº Grupo",
        compute="_compute_company_info",
        store=True,
        states=EDITABLE_ON_DRAFT,
    )
    exonerated_390 = fields.Selection(
        selection=[("1", "Exonerado"), ("2", "No exonerado")],
        default="2",
        required=True,
        states=EDITABLE_ON_DRAFT,
        readonly=True,
        string="Exonerado mod. 390",
        help="Exonerado de la Declaración-resumen anual del IVA, modelo 390: "
        "Volumen de operaciones (art. 121 LIVA)",
    )
    total_deducir = fields.Float(
        string="[62] Total a deducir", compute="_compute_total_deducir"
    )
    total_devengado = fields.Float(
        string="[38] Total devengador", compute="_compute_total_devengado"
    )
    casilla_63 = fields.Float(
        string="[63] General scheme result",
        readonly=True,
        store=True,
        help="(VAT payable - VAT receivable)",
        compute="_compute_casilla_63",
    )
    porcentaje_atribuible_estado = fields.Float(
        string="[64] % attributable to State",
        default=100,
        states=NON_EDITABLE_ON_DONE,
        help="Taxpayers who pay jointly to the Central Government and "
        "the Provincial Councils of the Basque Country or the "
        "Autonomous Community of Navarra, will enter in this box the "
        "percentage of volume operations in the common territory. "
        "Other taxpayers will enter in this box 100%",
    )
    atribuible_estado = fields.Float(
        string="[65] Attributable to the Administration",
        readonly=True,
        compute="_compute_atribuible_estado",
        store=True,
    )
    cuota_compensar = fields.Float(
        string="[66] Applied fees to compensate",
        default=0,
        states=NON_EDITABLE_ON_DONE,
        help="Fee to compensate for prior periods, in which his statement "
        "was to return and compensation back option was chosen",
    )
    cuota_liquidacion = fields.Float(
        string="[68] Result",
        default=0,
        states=NON_EDITABLE_ON_DONE,
        store=True,
        compute="_compute_cuota_liquidacion",
    )
    operaciones_ejercicio = fields.Float(
        string="[88] Operaciones realizadas en el ejercicio",
        store=True,
        default=0,
        compute="_compute_operaciones_ejercicio",
    )
    main_activity_code_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        domain=ACTIVITY_CODE_DOMAIN,
        states=NON_EDITABLE_ON_DONE,
        string="Código actividad principal",
    )
    main_activity_iae = fields.Char(
        states=NON_EDITABLE_ON_DONE,
        string="Epígrafe I.A.E. actividad principal",
        size=4,
    )
    counterpart_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Counterpart account",
        compute="_compute_counterpart_account_id",
        domain="[('company_id', '=', company_id)]",
        store=True,
        readonly=False,
    )
    allow_posting = fields.Boolean(string="Allow posting", default=True)

    @api.constrains("cuota_compensar")
    def check_qty(self):
        if self.filtered(lambda x: (x.cuota_compensar < 0)):
            raise ValidationError(
                _("The fee to compensate must be indicated as a positive number.")
            )

    def _compute_allow_posting(self):
        for report in self:
            report.allow_posting = True

    @api.depends("company_id", "cuota_liquidacion")
    def _compute_counterpart_account_id(self):
        for record in self:
            account_prefix = "4750"
            result = float_compare(
                record.cuota_liquidacion,
                0,
                precision_digits=record.currency_id.decimal_places,
            )
            if result == -1:
                account_prefix = "4700"
            code = ("%s%%" % account_prefix,)
            record.counterpart_account_id = self.env["account.account"].search(
                [("code", "=like", code[0]), ("company_id", "=", record.company_id.id)],
                limit=1,
            )

    @api.depends("tax_line_ids")
    def _compute_operaciones_ejercicio(self):
        for record in self:
            record.operaciones_ejercicio = sum(
                record.tax_line_ids.filtered(
                    lambda r: r.field_number
                    in [80, 81, 93, 94, 83, 84, 125, 126, 127, 128, 86, 95, 96, 97, 98]
                ).mapped("amount")
            ) - sum(
                record.tax_line_ids.filtered(
                    lambda r: r.field_number in [79, 99]
                ).mapped("amount")
                or [0.0]
            )

    @api.depends("atribuible_estado", "cuota_compensar")
    def _compute_cuota_liquidacion(self):
        for record in self:
            record.cuota_liquidacion = record.currency_id.round(
                record.atribuible_estado - record.cuota_compensar
            )

    @api.depends("total_devengado", "total_deducir")
    def _compute_casilla_63(self):
        for record in self:
            record.casilla_63 = record.currency_id.round(
                record.total_devengado - record.total_deducir
            )

    @api.depends("casilla_63", "porcentaje_atribuible_estado")
    def _compute_atribuible_estado(self):
        for record in self:
            record.atribuible_estado = record.currency_id.round(
                record.casilla_63 * record.porcentaje_atribuible_estado / 100.0
            )

    @api.depends("tax_line_ids")
    def _compute_total_devengado(self):
        for record in self:
            record.total_devengado = sum(
                record.tax_line_ids.filtered(
                    lambda r: r.field_number
                    in [
                        161,
                        3,
                        164,
                        6,
                        9,
                        152,
                        11,
                        14,
                        155,
                        17,
                        20,
                        22,
                        24,
                        26,
                        158,
                        29,
                        32,
                        35,
                        37,
                    ]
                ).mapped("amount")
            )

    @api.depends("tax_line_ids")
    def _compute_total_deducir(self):
        for record in self:
            record.total_deducir = sum(
                record.tax_line_ids.filtered(
                    lambda r: r.field_number
                    in [40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 59, 60, 61]
                ).mapped("amount")
            )

    @api.depends("company_id")
    def _compute_company_info(self):
        for record in self:
            mod322_group = self.env["l10n.es.aeat.mod322.group"].search(
                [
                    "|",
                    ("main_company_id", "=", record.company_id.id),
                    ("company_ids", "=", record.company_id.id),
                ]
            )
            if len(mod322_group) > 1:
                raise ValidationError(_("More than one configuration for the company"))
            if not len(mod322_group):
                record.group_number = False
                record.dominant_company_vat = re.match(
                    "(ES){0,1}(.*)", record.company_id.vat
                ).groups()[1]
                record.vinculated_partner_ids = False
                record.company_type = "D"
                continue
            record.group_number = mod322_group.name
            record.dominant_company_vat = re.match(
                "(ES){0,1}(.*)", mod322_group.main_company_id.vat
            ).groups()[1]
            record.company_type = (
                "P" if mod322_group.main_company_id == record.company_id else "D"
            )
            record.vinculated_partner_ids = (
                mod322_group.main_company_id.partner_id
                | mod322_group.company_ids.partner_id
                | mod322_group.vinculated_partner_ids
            )

    def _get_move_line_domain(self, date_start, date_end, map_line):
        domain = super()._get_move_line_domain(date_start, date_end, map_line)
        if map_line.field_number in [
            1,
            3,
            4,
            6,
            7,
            9,
            10,
            11,
            39,
            40,
            41,
            42,
            43,
            44,
            159,
            161,
            162,
            164,
        ]:
            domain.append(("partner_id", "in", self.vinculated_partner_ids.ids))
        if map_line.field_number in [
            12,
            14,
            15,
            17,
            18,
            20,
            25,
            26,
            45,
            46,
            47,
            48,
            57,
            58,
            150,
            151,
            152,
            153,
            154,
            155,
        ]:
            domain += [
                "|",
                ("partner_id", "=", False),
                ("partner_id", "not in", self.vinculated_partner_ids.ids),
            ]
        return domain

    def _get_tax_lines(self, date_start, date_end, map_line):
        """Don't populate results for fields 79-99 for reports different from
        last of the year one or when not exonerated of presenting model 390.
        """
        if 79 <= map_line.field_number <= 99 or map_line.field_number in [
            125,
            126,
            127,
        ]:
            if (
                self.exonerated_390 == "2"
                or not self.has_operation_volume
                or self.period_type not in ("4T", "12")
            ):
                return self.env["account.move.line"]
        return super()._get_tax_lines(
            date_start,
            date_end,
            map_line,
        )
