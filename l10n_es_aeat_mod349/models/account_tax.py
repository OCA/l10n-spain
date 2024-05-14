# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# Copyright 2018-2020 Tecnativa - Pedro M. Baeza
# Copyright 2024 Sygel - Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    def _selection_operation_key(self):
        return self.env["account.move.line"].fields_get(
            allfields=["l10n_es_aeat_349_operation_key"],
        )["l10n_es_aeat_349_operation_key"]["selection"]

    l10n_es_aeat_349_operation_key = fields.Selection(
        selection=_selection_operation_key,
        string="AEAT 349 Operation key",
        compute="_compute_l10n_es_aeat_349_operation_key",
        compute_sudo=True,
        search="_search_l10n_es_aeat_349_operation_key",
    )

    def _taxes_without_operation_key(self):
        map_349_lines = self.env["aeat.349.map.line"].search([])
        all_349_taxes_xmlid = map_349_lines.mapped("tax_xmlid_ids")
        all_349_taxes = map_349_lines._get_tax_ids_from_xmlids(all_349_taxes_xmlid)
        return list(set(self.env["account.tax"].search([]).ids) - set(all_349_taxes))

    def _search_l10n_es_aeat_349_operation_key(self, operator, value):
        tax_ids = []
        if operator == "=" and not value:
            tax_ids = self._taxes_without_operation_key()
        else:
            is_not_in = operator == "not in"
            if is_not_in:
                operator = "in"
            map_349_lines = self.env["aeat.349.map.line"].search(
                [("operation_key", operator, value)]
            )
            if map_349_lines:
                taxes_xmlid = map_349_lines.mapped("tax_xmlid_ids")
                tax_ids = map_349_lines._get_tax_ids_from_xmlids(
                    taxes_xmlid, self.env.company
                )
            if is_not_in:
                tax_ids = list(
                    set(self.env["account.tax"].search([]).ids) - set(tax_ids)
                )
            elif operator == "!=" and value:
                taxes_without_operation_key = self._taxes_without_operation_key()
                tax_ids += taxes_without_operation_key
        return [("id", "in", tax_ids)]

    def _compute_l10n_es_aeat_349_operation_key(self):
        # TODO: Improve performance
        map_349 = self.env["aeat.349.map.line"].search([])
        for tax in self:
            tax.l10n_es_aeat_349_operation_key = False
            for line in map_349:
                taxes_ids = line._get_tax_ids_from_xmlids(
                    line.tax_xmlid_ids, tax.company_id
                )
                if taxes_ids and tax.id in taxes_ids:
                    tax.l10n_es_aeat_349_operation_key = line.operation_key
                    break
