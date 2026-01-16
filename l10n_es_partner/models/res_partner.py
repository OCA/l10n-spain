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

    @api.depends("comercial")
    @api.depends_context("no_display_commercial")
    def _compute_display_name(self):
        super(
            ResPartner,
            self.with_context(
                display_commercial=not self.env.context.get(
                    "no_display_commercial", False
                )
            ),
        )._compute_display_name()
        name_pattern = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_es_partner.name_pattern", default="")
        )
        if not name_pattern:
            return
        for partner in self:
            if partner.comercial and partner.env.context.get("formatted_display_name"):
                partner.display_name = name_pattern % {
                    "name": partner.display_name,
                    "comercial_name": partner.comercial,
                }

    def _get_complete_name(self):
        name = super()._get_complete_name()
        if self.env.context.get("display_commercial") and self.comercial:
            name_pattern = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("l10n_es_partner.name_pattern", default="")
            )
            if name_pattern:
                name = name_pattern % {
                    "name": name,
                    "comercial_name": self.comercial,
                }
        return name

    @api.depends("comercial")
    def _compute_complete_name(self):
        # We are enforcing the new context,
        # because complete name field will remove the context
        res = super()._compute_complete_name()
        for partner in self:
            partner.complete_name = partner.with_context(
                display_commercial=not self.env.context.get(
                    "no_display_commercial", False
                )
            )._get_complete_name()
        return res

    @api.model
    def _commercial_fields(self):
        res = super()._commercial_fields()
        res += ["comercial"]
        return res

    @api.model
    @api.readonly
    def name_search(self, name="", domain=None, operator="ilike", limit=100):
        # Inject the field comercial in _rec_names_search if not exists
        if "comercial" not in self._rec_names_search:
            self._rec_names_search.append("comercial")
        return super().name_search(
            name=name, domain=domain, operator=operator, limit=limit
        )
