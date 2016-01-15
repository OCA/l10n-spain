# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class NumberName(models.AbstractModel):
    _description = "Base for tables with a number and a name"
    _name = "l10n.es.tgss.number_name"

    number = fields.Integer(index=True)
    name = fields.Char(index=True, translate=True)
    display_name = fields.Char(compute="_display_name_compute")

    _sql_constraints = [
        ('number_unique', 'unique (number)', 'Each number must be unique.'),
        ('name_unique', 'unique (name)', 'Each name must be unique.'),
    ]

    @api.multi
    @api.depends("number", "name")
    def _display_name_compute(self):
        """Combine number and name."""
        for s in self:
            s.combined = "%d. %s" % (s.number, s.name)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=20):
        """Faster search by number or name.

        This is because searching in computed fields is much slower, and
        storing translated values for computed fields is a pain.
        """
        args = list(args or list())
        split = name.split(".", 1)

        # Are you looking for something like "1. Name of group"?
        if len(split) == 2 and split[0].isnumeric():
            args.append(("number", operator, split[0]))
            args.append(("name", operator, split[1].lstrip()))

        # You are looking for either the code or the name
        else:
            field = "number" if name.isnumeric() else "name"
            args.append((field, operator, name))

        return self.search(args, limit=limit).name_get()
