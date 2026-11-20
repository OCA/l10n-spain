# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class L10nEsAeatTaxLine(models.Model):
    _name = "l10n.es.aeat.tax.line"
    _order = "field_number asc, id asc"
    _description = "AEAT tax line"

    res_id = fields.Integer(string="Resource ID", index=True, required=True)
    field_number = fields.Integer(
        string="Field number",
        related="map_line_id.field_number",
        store=True,
        readonly=True,
    )
    name = fields.Char(
        string="Name", related="map_line_id.name", store=True, readonly=True
    )
    amount = fields.Float(digits="Account")
    map_line_id = fields.Many2one(
        comodel_name="l10n.es.aeat.map.tax.line",
        string="Map line",
        required=True,
        ondelete="cascade",
    )
    move_line_ids = fields.Many2many(
        comodel_name="account.move.line", string="Journal items"
    )
    to_regularize = fields.Boolean(related="map_line_id.to_regularize", readonly=True)
    model = fields.Char(index=True, readonly=True, required=True, string="Model name")

    def get_calculated_move_lines(self):
        return self.env["l10n.es.aeat.report"]._view_move_lines(self.move_line_ids)
