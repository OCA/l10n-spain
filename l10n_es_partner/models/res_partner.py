# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2012-2014 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2016-2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    comercial = fields.Char("Trade name", size=128, index="trigram")
    display_name = fields.Char(compute="_compute_display_name")

    @api.depends("comercial")
    def _compute_display_name(self):
        return super()._compute_display_name()

    def _get_name(self):
        name_pattern = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_es_partner.name_pattern", default="")
        )
        origin = super()._get_name()
        if (
            self.env.context.get("no_display_commercial", False)
            or not name_pattern
            or not self.comercial
        ):
            return origin
        return name_pattern % {"name": origin, "comercial_name": self.comercial}

    @api.model
    def _commercial_fields(self):
        res = super()._commercial_fields()
        res += ["comercial"]
        return res

    def _auto_init(self):
        self.env["res.partner"]._rec_names_search.append("comercial")
        return super()._auto_init()
