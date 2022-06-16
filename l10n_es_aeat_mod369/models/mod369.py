# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class L10nEsAeatMod369Report(models.Model):
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.aeat.mod369.report"
    _description = "AEAT 369 Report"
    _aeat_number = "369"

    @api.depends("tax_line_ids")
    def _compute_total_amount(self):
        for report in self:
            tax_lines = report.tax_line_ids.filtered(
                lambda x: x.map_line_id.field_type == "amount"
            )
            report.total_amount = sum(tax_lines.mapped("amount"))

    services_line_ids = fields.One2many(
        string="Services 369 lines",
        comodel_name="l10n.es.aeat.mod369.line.grouped",
        inverse_name="report_id",
        domain=[("service_type", "=", "services")],
        copy=False,
        readonly=True,
    )
    spain_services_line_ids = fields.One2many(
        string="Spanish services 369 lines",
        comodel_name="l10n.es.aeat.mod369.line.grouped",
        inverse_name="report_id",
        domain=[("service_type", "=", "services"), ("country_id.code", "=", "ES")],
        copy=False,
        readonly=True,
    )
    goods_line_ids = fields.One2many(
        string="Goods 369 lines",
        comodel_name="l10n.es.aeat.mod369.line.grouped",
        inverse_name="report_id",
        domain=[("service_type", "=", "goods")],
        copy=False,
        readonly=True,
    )
    spain_goods_line_ids = fields.One2many(
        string="Spanish goods 369 lines",
        comodel_name="l10n.es.aeat.mod369.line.grouped",
        inverse_name="report_id",
        domain=[("service_type", "=", "goods"), ("country_id.code", "=", "ES")],
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
                country = tax_data.get("country", self.env["res.country"])
                tax = tax_data.get("tax", self.env["account.tax"])
                name = "Régimen Unión - OSS {} - {} {}%".format(
                    country.name,
                    "Base imponible" if map_line.field_type == "base" else "Cuota",
                    tax.amount,
                )
                mod369_line = self.env["l10n.es.aeat.mod369.line"].create(
                    {
                        "oss_name": name,
                        "oss_country_id": country.id,
                        "oss_tax_id": tax.id,
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
            for line in report.mapped("tax_line_ids").filtered(lambda l: l.amount > 0):
                mod369_line = line.mod369_line_id
                country = mod369_line.oss_country_id
                tax = mod369_line.oss_tax_id
                outside_spain = bool(country.code != "ES")
                key_country = "OUT-ES" if outside_spain else "ES"
                mod369_line.oss_sequence = lines_index[tax.service_type][key_country]
                lines_index[tax.service_type][key_country] += 1
                # page 3, 4, 5 or 6
                key = "{}{}{}{}".format(
                    country.id,
                    tax.id,
                    tax.service_type,
                    outside_spain,
                )
                country_groups.setdefault(
                    key,
                    {
                        "country_id": country.id,
                        "tax_id": tax.id,
                        "mod369_line_ids": [],
                        "report_id": report.id,
                    },
                )
                country_groups[key]["mod369_line_ids"] += [(4, mod369_line.id)]
                # page 8
                country_groups.setdefault(
                    country.id,
                    {
                        "country_id": country.id,
                        "tax_id": tax.id,
                        "mod369_line_ids": [],
                        "report_id": report.id,
                        "is_page_8_line": True,
                    },
                )
                country_groups[country.id]["mod369_line_ids"] += [(4, mod369_line.id)]
            self.env["l10n.es.aeat.mod369.line.grouped"].create(
                list(country_groups.values())
            )
        return res
