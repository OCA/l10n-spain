# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2012-2014 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2016,2022,2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    comercial = fields.Char("Trade name", size=128, index="trigram")
    display_name = fields.Char(compute="_compute_display_name")

    @api.depends("comercial")
    @api.depends_context("no_display_commercial")
    def _compute_display_name(self):
        """
        We are enforcing the new context,
        because complete name field will remove the context
        """
        return super(
            ResPartner,
            self.with_context(
                display_commercial=not self.env.context.get(
                    "no_display_commercial", False
                )
            ),
        )._compute_display_name()

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

    @api.model
    def _commercial_fields(self):
        res = super()._commercial_fields()
        res += ["comercial"]
        return res

    @property
    def _rec_names_search(self):
        # Inject the field comercial in _rec_names_search
        return list(set(super()._rec_names_search + ["comercial"]))

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options)
        # Inject the commercial field into the domain when searching by complete_name
        if "search" in res["views"]:
            res["views"]["search"]["arch"] = res["views"]["search"]["arch"].replace(
                "'|', ('complete_name', 'ilike', self)",
                "'|','|',('complete_name','ilike',self),('comercial','ilike',self)",
            )
        return res
