# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2012-2014 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2016,2022,2025 Tecnativa - Pedro M. Baeza
# Copyright 2025 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    comercial = fields.Char("Trade name", size=128, index="trigram")

    @property
    def _rec_names_search(self):
        """Search by trade name as well, keeping the search fields of the
        inherited models"""
        names = super()._rec_names_search
        if "comercial" in names:
            return names
        return [*names, "comercial"]

    def _get_name_with_commercial(self, name):
        """Name formatted with the trade name pattern, unless the context hides
        the trade name"""
        if not self.comercial or self.env.context.get("no_display_commercial"):
            return name
        name_pattern = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_str("l10n_es_partner.name_pattern", default="")
        )
        if not name_pattern:
            return name
        return name_pattern % {"name": name, "comercial_name": self.comercial}

    def _get_complete_name(self):
        return self._get_name_with_commercial(super()._get_complete_name())

    @api.depends("comercial")
    def _compute_complete_name(self):
        # Odoo core computes it without context, so the stored name, which sorts
        # the contacts and is shown in their list, always has the trade name
        return super()._compute_complete_name()

    @api.depends("comercial")
    @api.depends_context("no_display_commercial")
    def _compute_display_name(self):
        res = super()._compute_display_name()
        # The formatted name of Odoo core is not built from the complete name
        if self.env.context.get("formatted_display_name"):
            for partner in self:
                partner.display_name = partner._get_name_with_commercial(
                    partner.display_name
                )
        return res

    @api.model
    def _commercial_fields(self):
        res = super()._commercial_fields()
        res += ["comercial"]
        return res
