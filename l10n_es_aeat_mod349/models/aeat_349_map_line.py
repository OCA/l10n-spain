# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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
    tax_xmlid_ids = fields.Many2many(
        comodel_name="l10n.es.aeat.map.tax.line.tax", string="Taxes templates"
    )
    operation_key = fields.Selection(
        selection=_selection_operation_key,
        required=True,
    )

    @api.model
    def _get_tax_ids_from_xmlids(self, tax_templates, company=False):
        if not company:
            companies = self.env["res.company"].search([])
        else:
            companies = company
        taxes_ids = []
        for tax_template in tax_templates:
            for company in companies:
                tax_id = company._get_tax_id_from_xmlid(tax_template.name)
                if tax_id:
                    taxes_ids.append(tax_id)
        return taxes_ids
