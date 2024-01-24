# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# Copyright 2022 Tecnativa - Víctor Martínez
# Copyright 2023 Factor Libre - Aritz Olea
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class L10nEsAeatMod369LineGrouped(models.Model):
    _name = "l10n.es.aeat.mod369.line.grouped"
    _description = "Grouped info by country for 369 model"

    @api.depends("mod369_line_ids", "refund_line_ids")
    def _compute_totals(self):
        for group in self:
            group_keys = {
                "base": 0,
                "amount": 0,
                "page_3_total": 0,
                "page_4_total": 0,
                "page_3_4_total": 0,
                "page_5_total": 0,
                "page_6_total": 0,
                "page_5_6_total": 0,
                "pos_corrections": 0,
                "neg_corrections": 0,
                "result_total": 0,
                "total_deposit": 0,
                "total_return": 0,
            }
            report = group.report_id
            for line in group.mod369_line_ids:
                ref_move_lines = line.tax_line_id.move_line_ids.filtered(
                    lambda ml: ml.move_type == "out_refund"
                    and ml.move_id.reversed_entry_id
                    and ml.move_id.reversed_entry_id.invoice_date < report.date_start
                )
                move_lines = line.tax_line_id.move_line_ids - ref_move_lines
                amount = sum(move_lines.mapped("credit"))
                amount -= sum(move_lines.mapped("debit"))
                group_keys[line.map_line_id.field_type] += amount
                if not group.is_page_8_line or line.map_line_id.field_type != "amount":
                    continue
                if line.country_id.code == "ES":
                    if line.service_type == "services":
                        group_keys["page_3_total"] += amount
                    elif line.service_type == "goods":
                        group_keys["page_4_total"] += amount
                else:
                    if line.service_type == "services":
                        group_keys["page_5_total"] += amount
                    elif line.service_type == "goods":
                        group_keys["page_6_total"] += amount
                group_keys["page_3_4_total"] = (
                    group_keys["page_3_total"] + group_keys["page_4_total"]
                )
                group_keys["page_5_6_total"] = (
                    group_keys["page_5_total"] + group_keys["page_6_total"]
                )

            if group.is_page_8_line:
                refund_line = self.env["l10n.es.aeat.mod369.line.grouped"].search(
                    [
                        ("report_id", "=", group.report_id.id),
                        ("is_refund", "=", True),
                        ("country_code", "=", group.country_code),
                    ],
                    limit=1,
                )
                if refund_line:
                    group_keys["neg_corrections"] = refund_line.tax_correction
                group_keys["result_total"] = (
                    group_keys["amount"]
                    + group_keys["pos_corrections"]
                    + group_keys["neg_corrections"]
                )
                if group_keys["result_total"] > 0:
                    group_keys["total_deposit"] = group_keys["result_total"]
                else:
                    group_keys["total_return"] = abs(group_keys["result_total"])
            group.update(group_keys)

    mod369_line_ids = fields.Many2many(
        string="Mod369 lines",
        comodel_name="l10n.es.aeat.mod369.line",
    )
    refund_line_ids = fields.Many2many(
        string="Refund lines",
        relation="refund_line_id_rel",
        comodel_name="account.move.line",
    )
    report_id = fields.Many2one(
        string="Mod369 report", comodel_name="l10n.es.aeat.mod369.report"
    )
    country_id = fields.Many2one(string="Country", comodel_name="res.country")
    oss_country_id = fields.Many2one(string="OSS Country", comodel_name="res.country")
    country_code = fields.Char(
        string="Country code", compute="_compute_country_code", store=True
    )
    tax_id = fields.Many2one(string="Tax", comodel_name="account.tax")
    vat_type = fields.Float(string="VAT Type", related="tax_id.amount")
    vat_type_str = fields.Char(compute="_compute_vat_type_str")
    service_type = fields.Selection(
        related="tax_id.service_type",
        string="Service type",
    )
    base = fields.Float(string="Base total", compute="_compute_totals")
    base_str = fields.Char(compute="_compute_base_str")
    amount = fields.Float(string="Amount total", compute="_compute_totals")
    amount_str = fields.Char(compute="_compute_amount_str")
    is_refund = fields.Boolean()
    refund_fiscal_year = fields.Integer()
    refund_period = fields.Char()
    tax_correction = fields.Float()
    tax_correction_str = fields.Char(compute="_compute_tax_correction_str")
    # page 8 fields
    is_page_8_line = fields.Boolean(
        string="Is part of page 8", help="Used to filter for grouped lines for page 8"
    )
    page_3_total = fields.Float(string="Spanish services", compute="_compute_totals")
    page_4_total = fields.Float(string="Spanish goods", compute="_compute_totals")
    page_3_4_total = fields.Float(
        string="Spanish services and goods", compute="_compute_totals"
    )
    page_5_total = fields.Float(
        string="Non-Spanish services", compute="_compute_totals"
    )
    page_6_total = fields.Float(string="Non-Spanish goods", compute="_compute_totals")
    page_5_6_total = fields.Float(
        string="Non-Spanish services and goods", compute="_compute_totals"
    )
    pos_corrections = fields.Float(string="Positive corrections")
    neg_corrections = fields.Float(string="Negative corrections")
    result_total = fields.Float(string="Total result")
    total_deposit = fields.Float(string="Total to deposit ES")
    total_return = fields.Float(string="Total to return EM")

    @api.depends("vat_type")
    def _compute_vat_type_str(self):
        for line in self:
            vat_type_split = str(line.vat_type).split(".")
            line.vat_type_str = vat_type_split[0].zfill(3) + vat_type_split[1].zfill(2)

    @api.depends("base")
    def _compute_base_str(self):
        for line in self:
            base_split = str(line.base).split(".")
            line.base_str = base_split[0].zfill(15) + base_split[1].zfill(2)

    @api.depends("amount")
    def _compute_amount_str(self):
        for line in self:
            amount_split = str(line.amount).split(".")
            line.amount_str = amount_split[0].zfill(15) + amount_split[1].zfill(2)

    @api.depends("tax_correction")
    def _compute_tax_correction_str(self):
        for line in self:
            tax_correction_split = str(line.tax_correction).split(".")
            line.tax_correction_str = tax_correction_split[0].zfill(
                15
            ) + tax_correction_split[1].zfill(2)

    @api.depends("oss_country_id", "oss_country_id.code")
    def _compute_country_code(self):
        for line in self:
            line.country_code = self.env["res.partner"]._map_aeat_country_iso_code(
                line.oss_country_id
            )

    def get_calculated_move_lines(self):
        res = self.env.ref("account.action_account_moves_all_a").sudo().read()[0]
        view = self.env.ref("l10n_es_aeat.view_move_line_tree")
        res["views"] = [(view.id, "tree")]
        move_lines = self.mapped("mod369_line_ids.tax_line_id.move_line_ids")
        ref_move_lines = move_lines.filtered(
            lambda ml: ml.move_type == "out_refund"
            and ml.move_id.reversed_entry_id
            and ml.move_id.reversed_entry_id.invoice_date < self.report_id.date_start
        )
        res["domain"] = [("id", "in", (move_lines - ref_move_lines).ids)]
        return res

    def get_calculated_refund_move_lines(self):
        res = self.env.ref("account.action_account_moves_all_a").sudo().read()[0]
        view = self.env.ref("l10n_es_aeat.view_move_line_tree")
        res["views"] = [(view.id, "tree")]
        res["domain"] = [("id", "in", self.mapped("refund_line_ids").ids)]
        return res
