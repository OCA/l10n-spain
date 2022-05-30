# Copyright 2013-2018 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from collections import defaultdict

from odoo import api, fields, models


class L10nEsAeatMapTaxLine(models.Model):
    _name = "l10n.es.aeat.map.tax.line"
    _order = "field_number asc, id asc"
    _description = "AEAT tax mapping line"

    field_number = fields.Integer(string="Field number", required=True)
    tax_ids = fields.Many2many(
        comodel_name="account.tax.template", string="Taxes templates"
    )
    fiscal_position_ids = fields.Many2many(
        comodel_name="account.fiscal.position.template",
        string="Fiscal Position Templates",
        compute="_compute_fiscal_position_ids",
        store=True,
        compute_sudo=True,
        help="Taxes mapped with different source tax on this Fiscal Position Templates",
    )
    account_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Account Template",
    )
    name = fields.Char(string="Name", required=True)
    map_parent_id = fields.Many2one(comodel_name="l10n.es.aeat.map.tax", required=True)
    move_type = fields.Selection(
        selection=[("all", "All"), ("regular", "Regular"), ("refund", "Refund")],
        string="Operation type",
        default="all",
        required=True,
    )
    field_type = fields.Selection(
        selection=[("base", "Base"), ("amount", "Amount"), ("both", "Both")],
        string="Field type",
        default="amount",
        required=True,
    )
    sum_type = fields.Selection(
        selection=[
            ("credit", "Credit"),
            ("debit", "Debit"),
            ("both", "Both (Credit - Debit)"),
        ],
        string="Summarize type",
        default="both",
        required=True,
    )
    exigible_type = fields.Selection(
        selection=[
            ("yes", "Only exigible amounts"),
            ("no", "Only non-exigible amounts"),
            ("both", "Both exigible and non-exigible amounts"),
        ],
        required=True,
        string="Exigibility",
        default="yes",
    )
    inverse = fields.Boolean(string="Inverse summarize sign", default=False)
    to_regularize = fields.Boolean(string="To regularize")

    @api.depends("tax_ids")
    def _compute_fiscal_position_ids(self):
        afpt_model = self.env["account.fiscal.position.tax.template"]
        afpt_map = defaultdict(list)
        for afpt_data in afpt_model.search_read(
            [
                ("tax_dest_id", "in", self.mapped("tax_ids").ids),
                ("position_id", "!=", False),
            ],
            ["position_id", "tax_dest_id", "tax_src_id"],
        ):
            # Exclude Fiscal Position Templates if source tax == dest tax
            if afpt_data["tax_src_id"][0] != afpt_data["tax_dest_id"][0]:
                afpt_map[afpt_data["tax_dest_id"][0]].append(
                    afpt_data["position_id"][0]
                )

        for map_tax_line in self:
            fiscal_position_list_ids = []
            for tax_id in map_tax_line.tax_ids.ids:
                fiscal_position_list_ids.extend(afpt_map.get(tax_id, []))
            map_tax_line.fiscal_position_ids = fiscal_position_list_ids
