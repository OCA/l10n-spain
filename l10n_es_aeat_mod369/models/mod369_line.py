# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class L10nEsAeatMod369Line(models.Model):
    _name = "l10n.es.aeat.mod369.line"
    _description = "Extra info for 369 model"

    tax_line_id = fields.Many2one(
        string="Report tax line",
        comodel_name="l10n.es.aeat.tax.line",
        ondelete="cascade",
    )
    oss_name = fields.Char(string="OSS Name")
    oss_tax_id = fields.Many2one(string="OSS Tax", comodel_name="account.tax")
    oss_country_id = fields.Many2one(string="OSS Country", comodel_name="res.country")
    oss_sequence = fields.Integer(string="OSS Sequence")
    outside_spain = fields.Boolean(string="Outside of Spain")
    service_type = fields.Selection(
        string="Service type", selection=[("goods", "Goods"), ("services", "Services")]
    )
    oss_regimen = fields.Selection(
        string="OSS Regimen",
        selection=[("union", "Union"), ("exterior", "Exterior"), ("import", "Import")],
    )
    field_number = fields.Integer(
        string="Field number", related="tax_line_id.field_number"
    )
    amount = fields.Float(string="Amount", related="tax_line_id.amount")
    map_line_id = fields.Many2one(
        string="Map line",
        comodel_name="l10n.es.aeat.map.tax.line",
        related="tax_line_id.map_line_id",
    )
    group_ids = fields.Many2many(
        string="Group", comodel_name="l10n.es.aeat.mod369.line.grouped"
    )
