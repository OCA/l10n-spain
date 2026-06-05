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
        xmlids = self.env["aeat.349.map.line"].search([]).tax_xmlid_ids.mapped("name")  # pylint: disable=W8163
        taxes = self.env["account.tax"].search([])  # pylint: disable=W8163
        for company in self.env.companies:
            taxes -= company._get_taxes_from_xmlids(xmlids)
        return taxes.ids

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
                xmlids = map_349_lines.tax_xmlid_ids.mapped("name")
                taxes = self.env["account.tax"]
                for company in self.env.companies:
                    taxes |= company._get_taxes_from_xmlids(xmlids)
                tax_ids = taxes.ids
            if is_not_in:
                tax_ids = list(
                    set(
                        self.env["account.tax"]
                        .search([("id", "not in", set(tax_ids))])
                        .ids
                    )
                )
            elif operator == "!=" and value:
                taxes_without_operation_key = self._taxes_without_operation_key()
                tax_ids += taxes_without_operation_key
        return [("id", "in", tax_ids)]

    def _compute_l10n_es_aeat_349_operation_key(self):
        self.l10n_es_aeat_349_operation_key = False
        for company in self.company_id:
            for rec in self.env["aeat.349.map.line"].search([]):  # pylint: disable=W8163
                taxes = company._get_taxes_from_xmlids(rec.tax_xmlid_ids.mapped("name"))
                (self & taxes).l10n_es_aeat_349_operation_key = rec.operation_key
