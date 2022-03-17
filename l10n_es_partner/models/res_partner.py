# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2012-2014 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# Copyright 2016-2022 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo import api, fields, models
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = "res.partner"

    comercial = fields.Char("Trade name", size=128, index=True)

    # Extend original depends with comercial field
    @api.depends("comercial")
    def _compute_display_name(self):
        return super()._compute_display_name()

    @api.model
    def _get_comercial_name_pattern(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_es_partner.name_pattern", default="")
        )

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Include commercial name in direct name search."""
        if "%(comercial_name)s" not in self._get_comercial_name_pattern():
            args = expression.normalize_domain(args)
            for arg in args:
                if (
                    isinstance(arg, (list, tuple))
                    and (arg[0] == "name" or arg[0] == "display_name")
                    and arg[2]
                ):
                    index = args.index(arg)
                    args = (
                        args[:index]
                        + ["|", ("comercial", arg[1], arg[2])]
                        + args[index:]
                    )
                    break
        return super().search(
            args, offset=offset, limit=limit, order=order, count=count
        )

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        """Give preference to commercial names on name search, appending
        the rest of the results after. This has to be done this way, as
        Odoo overwrites name_search on res.partner in a non inheritable way."""
        if "%(comercial_name)s" in self._get_comercial_name_pattern():
            return super().name_search(
                name=name, args=args, operator=operator, limit=limit
            )
        if not args:
            args = []
        partner_search_mode = self.env.context.get("res_partner_search_mode")
        order = "{}_rank".format(partner_search_mode) if partner_search_mode else None
        partners = self.search(
            [("comercial", operator, name)] + args, limit=limit, order=order
        )
        res = models.lazy_name_get(partners)
        if limit:
            limit_rest = limit - len(partners)
        else:  # pragma: no cover
            # limit can be 0 or None representing infinite
            limit_rest = limit
        if limit_rest or not limit:
            args += [("id", "not in", partners.ids)]
            res += super().name_search(
                name, args=args, operator=operator, limit=limit_rest
            )
        return res

    def _get_name(self):
        name_pattern = self._get_comercial_name_pattern()
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
