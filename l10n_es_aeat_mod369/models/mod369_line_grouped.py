# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class L10nEsAeatMod369LineGrouped(models.Model):
    _name = "l10n.es.aeat.mod369.line.grouped"
    _description = "Grouped info by country for 369 model"

    @api.depends("mod369_line_ids")
    def _compute_totals(self):
        for group in self:
            base = 0
            amount = 0
            page_3_total = 0
            page_4_total = 0
            page_3_4_total = 0
            page_5_total = 0
            page_6_total = 0
            page_5_6_total = 0
            for line in group.mod369_line_ids:
                if line.map_line_id.field_type == "base":
                    base += line.amount
                elif line.map_line_id.field_type == "amount":
                    amount += line.amount
                if not group.is_page_8_line or line.map_line_id.field_type != "amount":
                    continue
                if not line.outside_spain:
                    if line.service_type == "services":
                        page_3_total += line.amount
                    elif line.service_type == "goods":
                        page_4_total += line.amount
                else:
                    if line.service_type == "services":
                        page_5_total += line.amount
                    elif line.service_type == "goods":
                        page_6_total += line.amount
                page_3_4_total = page_3_total + page_4_total
                page_5_6_total = page_5_total + page_6_total
            group.update(
                {
                    "base": base,
                    "amount": amount,
                    "page_3_total": page_3_total,
                    "page_4_total": page_4_total,
                    "page_3_4_total": page_3_4_total,
                    "page_5_total": page_5_total,
                    "page_6_total": page_6_total,
                    "page_5_6_total": page_5_6_total,
                }
            )

    mod369_line_ids = fields.Many2many(
        string="Mod369 lines",
        comodel_name="l10n.es.aeat.mod369.line",
        inverse_name="group_id",
    )
    report_id = fields.Many2one(
        string="Mod369 report", comodel_name="l10n.es.aeat.mod369.report"
    )
    country_id = fields.Many2one(string="Country", comodel_name="res.country")
    country_code = fields.Char(string="Country code", related="country_id.code")
    tax_id = fields.Many2one(string="Tax", comodel_name="account.tax")
    vat_type = fields.Float(string="VAT Type", related="tax_id.amount")
    outside_spain = fields.Boolean(string="Outside of Spain")
    service_type = fields.Selection(
        string="Service type", selection=[("goods", "Goods"), ("services", "Services")]
    )
    base = fields.Float(string="Base", compute="_compute_totals")
    amount = fields.Float(string="Amount", compute="_compute_totals")
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

    def get_calculated_move_lines(self):
        res = self.env.ref("account.action_account_moves_all_a").sudo().read()[0]
        view = self.env.ref("l10n_es_aeat.view_move_line_tree")
        res["views"] = [(view.id, "tree")]
        res["domain"] = [
            ("id", "in", self.mapped("mod369_line_ids.tax_line_id.move_line_ids").ids)
        ]
        return res
