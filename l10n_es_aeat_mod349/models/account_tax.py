# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# Copyright 2018-2020 Tecnativa - Pedro M. Baeza
# Copyright 2024 Sygel - Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import Domain


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

    def _l10n_es_aeat_349_tags(self):
        """Map the ids of the 349 tags that Odoo core puts on the base lines of the
        Spanish taxes (``mod349[X]``) to their operation key."""
        tags = {}
        for key, _label in self._selection_operation_key():
            tag = self.env.ref(
                f"l10n_es.account_tag_mod349_{key}", raise_if_not_found=False
            )
            if tag:
                tags[tag.id] = key
        return tags

    def _search_l10n_es_aeat_349_operation_key(self, operator, value):
        if operator != "in":
            return NotImplemented
        tags = self._l10n_es_aeat_349_tags()
        domain = Domain(
            "invoice_repartition_line_ids.tag_ids",
            "in",
            [tag_id for tag_id, key in tags.items() if key in value],
        )
        if False in value:
            domain |= ~Domain("invoice_repartition_line_ids.tag_ids", "in", list(tags))
        return domain

    @api.depends("invoice_repartition_line_ids.tag_ids")
    def _compute_l10n_es_aeat_349_operation_key(self):
        tags = self._l10n_es_aeat_349_tags()
        for tax in self:
            tax.l10n_es_aeat_349_operation_key = next(
                (
                    tags[tag.id]
                    for tag in tax.invoice_repartition_line_ids.tag_ids
                    if tag.id in tags
                ),
                False,
            )
