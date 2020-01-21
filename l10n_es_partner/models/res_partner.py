# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2012-2014 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# Copyright 2016 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo import api, fields, models
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = "res.partner"

    comercial = fields.Char("Trade name", size=128, index=True)
    display_name = fields.Char(compute="_compute_display_name")

    @api.depends("comercial")
    def _compute_display_name(self):
        super()._compute_display_name()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Include commercial name in direct name search."""
        args = expression.normalize_domain(args)
        for arg in args:
            if isinstance(arg, (list, tuple)) and (
                arg[0] == "name" or arg[0] == "display_name"
            ):
                index = args.index(arg)
                args = (
                    args[:index] + ["|", ("comercial", arg[1], arg[2])] + args[index:]
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
        if not args:
            args = []
        partners = self.search([("comercial", operator, name)] + args, limit=limit)
        res = partners.name_get()
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

    def name_get(self):
        result = []
        name_pattern = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_es_partner.name_pattern", default="")
        )
        origin = super().name_get()
        if self.env.context.get("no_display_commercial", False):
            return origin
        orig_name = dict(origin)
        for partner in self:
            name = orig_name[partner.id]
            comercial = partner.comercial
            if comercial and name_pattern:
                name = name_pattern % {"name": name, "comercial_name": comercial}
            result.append((partner.id, name))
        return result

    @api.model
    def _commercial_fields(self):
        res = super()._commercial_fields()
        res += ["comercial"]
        return res
