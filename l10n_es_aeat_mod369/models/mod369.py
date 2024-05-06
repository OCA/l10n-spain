# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# Copyright 2022 Tecnativa - Víctor Martínez
# Copyright 2023 Factor Libre - Aritz Olea
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class L10nEsAeatMod369Report(models.Model):
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod369.report"
    _description = "AEAT 369 Report"
    _aeat_number = "369"

    @api.depends("tax_line_ids")
    def _compute_total_amount(self):
        for report in self:
            total_lines = report.total_line_ids
            report.total_amount = sum(total_lines.mapped("total_deposit"))

    services_line_ids = fields.One2many(
        string="Services 369 lines",
        comodel_name="l10n.es.aeat.mod369.line.grouped",
        inverse_name="report_id",
        domain=[
            ("service_type", "=", "services"),
            ("is_refund", "=", False),
        ],
        copy=False,
        readonly=True,
    )
    spain_services_line_ids = fields.One2many(
        string="Spanish services 369 lines",
        comodel_name="l10n.es.aeat.mod369.line.grouped",
        inverse_name="report_id",
        domain=[
            ("service_type", "=", "services"),
            ("country_id.code", "=", "ES"),
            ("is_page_8_line", "=", False),
            ("is_refund", "=", False),
        ],
        copy=False,
        readonly=True,
    )
    goods_line_ids = fields.One2many(
        string="Goods 369 lines",
        comodel_name="l10n.es.aeat.mod369.line.grouped",
        inverse_name="report_id",
        domain=[
            ("service_type", "=", "goods"),
            ("is_refund", "=", False),
        ],
        copy=False,
        readonly=True,
    )
    spain_goods_line_ids = fields.One2many(
        string="Spanish goods 369 lines",
        comodel_name="l10n.es.aeat.mod369.line.grouped",
        inverse_name="report_id",
        domain=[
            ("service_type", "=", "goods"),
            ("country_id.code", "=", "ES"),
            ("is_page_8_line", "=", False),
            ("is_refund", "=", False),
        ],
        copy=False,
        readonly=True,
    )
    refund_line_ids = fields.One2many(
        string="Refunds from other periods 369 lines",
        comodel_name="l10n.es.aeat.mod369.line.grouped",
        inverse_name="report_id",
        domain=[
            ("is_refund", "=", True),
        ],
        copy=False,
        readonly=True,
    )
    total_line_ids = fields.One2many(
        string="Total 369 lines",
        comodel_name="l10n.es.aeat.mod369.line.grouped",
        inverse_name="report_id",
        domain=[("is_page_8_line", "=", True)],
        copy=False,
        readonly=True,
    )
    total_amount = fields.Float(string="Total amount", compute="_compute_total_amount")
    declaration_type = fields.Selection(
        string="Declaration type",
        selection=[("union", "Union"), ("export", "Export"), ("import", "Import")],
        readonly=True,
        default="union",
        states={"draft": [("readonly", False)]},
    )
    nrc_reference = fields.Char(
        string="NRC Reference",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
    )
    declaration_inactive = fields.Boolean(
        string="Declaration without activity",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    payment_type = fields.Selection(
        selection=[
            (
                "O",
                "[O] Reconocimiento de deuda con los Estados "
                "Miembros de Consumo con imposibilidad de pago",
            ),
            (
                "S",
                "[S] Ingreso parcial y Reconocimiento de deuda "
                "con los Estados Miembros de Consumo con imposibilidad de pago",
            ),
            ("I", "[I] A ingresar"),
            ("N", "[N] Negativa"),
            ("T", "[T] Ingreso por transferencia desde el extranjero"),
        ],
        string="Payment type",
        default="I",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    def _compute_allow_posting(self):
        self.allow_posting = True

    @api.model
    def _get_period_from_date(self, date, monthly=False):
        month = date.month
        if not monthly:
            if month in [1, 2, 3]:
                return "T1"
            elif month in [4, 5, 6]:
                return "T2"
            elif month in [7, 8, 9]:
                return "T3"
            else:
                return "T4"
        else:
            return "M" + str(month)

    def get_taxes_from_map(self, map_line):
        oss_map_lines = self.env.context.get("oss_map_lines", {})
        if map_line in oss_map_lines:
            oss_taxes_map = self.env.context.get("oss_taxes_map", {})
            return oss_taxes_map.get(map_line.field_number, {}).get(
                "tax", self.env["account.tax"]
            )
        return super().get_taxes_from_map(map_line)

    def _get_oss_taxes_map(self):
        oss_taxes = self.env["account.tax"].search(
            [("oss_country_id", "!=", False), ("company_id", "=", self.company_id.id)]
        )
        oss_countries = {}
        for tax in oss_taxes:
            oss_countries.setdefault(tax.oss_country_id, self.env["account.tax"])
            oss_countries[tax.oss_country_id] |= tax
        oss_taxes_map = {}
        line_number = 1
        previous_country = False
        previous_tax_count = 0
        for country, taxes in oss_countries.items():
            if previous_country and country != previous_country:
                line_number += 8 - (previous_tax_count * 2)
                previous_tax_count = 0
            for tax in taxes:
                previous_tax_count += 1
                oss_taxes_map.update(
                    {
                        # Goods + spain (base)
                        line_number: {"tax": tax, "country": country},
                        # Goods + spain (amount)
                        line_number + 1: {"tax": tax, "country": country},
                        # Goods + outside spain (base)
                        line_number + 224: {"tax": tax, "country": country},
                        # Goods + outside spain (amount)
                        line_number + 225: {"tax": tax, "country": country},
                        # Services + spain (base)
                        line_number + 448: {"tax": tax, "country": country},
                        # Services + spain (amount)
                        line_number + 449: {"tax": tax, "country": country},
                        # Services + outside spain (base)
                        line_number + 672: {"tax": tax, "country": country},
                        # Services + outside spain (amount)
                        line_number + 673: {"tax": tax, "country": country},
                    }
                )
                line_number += 2
            previous_country = country
        return oss_taxes_map

    def _prepare_tax_line_vals(self, map_line):
        self.ensure_one()
        oss_map_lines = self.env.context.get("oss_map_lines", {})
        new_vals = {}
        if map_line in oss_map_lines:
            oss_taxes_map = self.env.context.get("oss_taxes_map", {})
            tax_data = oss_taxes_map.get(map_line.field_number, {})
            if tax_data:
                tax = tax_data.get("tax", self.env["account.tax"])
                country = tax.country_id
                oss_country = tax.oss_country_id
                name = "Régimen Unión - OSS {} - {} {}%".format(
                    country.name,
                    "Base imponible" if map_line.field_type == "base" else "Cuota",
                    tax.amount,
                )
                mod369_line = self.env["l10n.es.aeat.mod369.line"].create(
                    {
                        "oss_name": name,
                        "oss_country_id": oss_country.id,
                        "oss_tax_id": tax.id,
                        "country_id": country.id,
                    }
                )
                new_vals = {"mod369_line_id": mod369_line.id}
        vals = super()._prepare_tax_line_vals(map_line=map_line)
        if new_vals:
            vals = dict(**vals, **new_vals)
        return vals

    def calculate(self):
        self.mapped("tax_line_ids.mod369_line_id").unlink()
        self.mapped("spain_goods_line_ids").unlink()
        self.mapped("spain_services_line_ids").unlink()
        self.mapped("refund_line_ids").unlink()
        self.mapped("total_line_ids").unlink()
        # Send through context so we only calculate these fixed values once
        oss_map_lines = self.env.ref("l10n_es_aeat_mod369.aeat_mod369_map").map_line_ids
        oss_taxes_map = self._get_oss_taxes_map()
        _self = self.with_context(
            oss_map_lines=oss_map_lines, oss_taxes_map=oss_taxes_map
        )
        res = super(L10nEsAeatMod369Report, _self).calculate()
        for report in self:
            # Remove placeholder lines and 0.0% as these shouldn't appear in the file
            report.mapped("tax_line_ids").filtered(
                lambda l: (
                    not l.mod369_line_id.oss_name
                    or " 0.0%" in l.mod369_line_id.oss_name
                )
            ).unlink()
            # Seperate sequence per "type" to filter easily in export.config.lines
            lines_index = {
                "goods": {"ES": 1, "OUT-ES": 1},
                "services": {"ES": 1, "OUT-ES": 1},
            }
            country_groups = {}
            tax_lines = report.mapped("tax_line_ids")
            for line in tax_lines.filtered(lambda tl: len(tl.move_line_ids) > 0):
                mod369_line = line.mod369_line_id
                ref_move_lines = line.move_line_ids.filtered(
                    lambda ml: ml.move_type == "out_refund"
                    and ml.move_id.reversed_entry_id
                    and ml.move_id.reversed_entry_id.invoice_date < report.date_start
                )
                move_lines = line.move_line_ids - ref_move_lines
                country = mod369_line.country_id
                oss_country = mod369_line.oss_country_id
                tax = mod369_line.oss_tax_id
                outside_spain = bool(country.code != "ES")
                key_country = "OUT-ES" if outside_spain else "ES"
                mod369_line.oss_sequence = lines_index[tax.service_type][key_country]
                lines_index[tax.service_type][key_country] += 1
                if len(move_lines) > 0:
                    # page 3, 4, 5 or 6
                    key = "{}{}{}{}".format(
                        oss_country.id,
                        tax.id,
                        tax.service_type,
                        outside_spain,
                    )
                    country_groups.setdefault(
                        key,
                        {
                            "country_id": country.id,
                            "oss_country_id": oss_country.id,
                            "tax_id": tax.id,
                            "mod369_line_ids": [],
                            "refund_line_ids": [],
                            "report_id": report.id,
                        },
                    )
                    country_groups[key]["mod369_line_ids"] += [(4, mod369_line.id)]
                # page 8
                country_groups.setdefault(
                    oss_country.id,
                    {
                        "country_id": country.id,
                        "oss_country_id": oss_country.id,
                        "tax_id": tax.id,
                        "mod369_line_ids": [],
                        "refund_line_ids": [],
                        "report_id": report.id,
                        "is_page_8_line": True,
                    },
                )
                country_groups[oss_country.id]["mod369_line_ids"] += [
                    (4, mod369_line.id)
                ]
                for mline in ref_move_lines:
                    orig_move = mline.move_id.reversed_entry_id
                    refund_fiscal_year = orig_move.date.year
                    monthly = report.period_type not in ["1T", "2T", "3T", "4T"]
                    refund_period = self._get_period_from_date(orig_move.date, monthly)
                    key = "{}{}{}".format(
                        oss_country.id,
                        refund_fiscal_year,
                        refund_period,
                    )
                    # page 7
                    country_groups.setdefault(
                        key,
                        {
                            "country_id": country.id,
                            "oss_country_id": oss_country.id,
                            "mod369_line_ids": [],
                            "refund_line_ids": [],
                            "report_id": report.id,
                            "is_refund": True,
                            "refund_fiscal_year": refund_fiscal_year,
                            "refund_period": refund_period,
                            "tax_correction": 0,
                        },
                    )
                    if line.map_line_id.field_type == "amount":
                        country_groups[key]["tax_correction"] -= mline.debit
                    country_groups[key]["refund_line_ids"] += [(4, mline.id)]

            groups = self.env["l10n.es.aeat.mod369.line.grouped"].create(
                list(country_groups.values())
            )
            groups._compute_totals()
        return res

    def _prepare_regularization_extra_move_lines(self):
        lines = super()._prepare_regularization_extra_move_lines()
        if self.total_amount > 0:
            account_template = self.env.ref("l10n_es.account_common_4750")
            account_4750 = self.company_id.get_account_from_template(account_template)
            lines.append(
                {
                    "name": account_4750.name,
                    "account_id": account_4750.id,
                    "debit": 0,
                    "credit": self.total_amount,
                }
            )
        elif self.total_amount < 0:
            account_template = self.env.ref("l10n_es.account_common_4700")
            account_4700 = self.company_id.get_account_from_template(account_template)
            lines.append(
                {
                    "name": account_4700.name,
                    "account_id": account_4700.id,
                    "debit": -self.total_amount,
                    "credit": 0,
                }
            )
        return lines

    @api.model
    def _prepare_counterpart_move_line(self, account, debit, credit):
        vals = super()._prepare_counterpart_move_line(account, debit, credit)
        vals.update({"name": account.name, "partner_id": False})
        return vals

    def create_regularization_move(self):
        self.ensure_one()
        if self.total_amount != 0:
            return super().create_regularization_move()
        else:
            raise UserError(
                _("It is not possible to create a move if the total amount is 0.")
            )
