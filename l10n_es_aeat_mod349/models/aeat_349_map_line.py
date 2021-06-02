# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Aeat349MapLines(models.Model):
    _name = "aeat.349.map.line"
    _description = "Aeat 349 Map Line"
    _rec_name = "operation_key"

    _sql_constraints = [
        (
            "unique_operation_key",
            "UNIQUE(operation_key)",
            "There's already another record with the same operation key",
        ),
    ]

    def _selection_operation_key(self):
        return self.env["account.move.line"].fields_get(
            allfields=["l10n_es_aeat_349_operation_key"],
        )["l10n_es_aeat_349_operation_key"]["selection"]

    physical_product = fields.Boolean(string="Involves physical product")
    tax_tmpl_ids = fields.One2many(
        comodel_name="account.tax.template",
        inverse_name="aeat_349_map_line",
        string="Taxes",
    )
    operation_key = fields.Selection(
        selection=_selection_operation_key,
        required=True,
    )
