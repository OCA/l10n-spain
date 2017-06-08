# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


def smart_search(self, name="", args=None, operator="ilike", limit=20,
                 number_field="number", name_field="name"):
    """Faster search by number or name.

    This is because searching in computed fields is much slower, and
    storing translated values for computed fields is a pain.

    Parameters work like :meth:`openerp.models.Model.name_search`'s, plus:

    :param str number_field:
        Name of the model's *number* field.

    :param str name_field:
        Name of the model's *name* field.
    """
    args = list(args or list())
    split = name.split(".", 1)

    # Are you looking for something like "1. Name of group"?
    if len(split) == 2 and split[0].isnumeric():
        args.append((number_field, operator, split[0]))
        args.append((name_field, operator, split[1].lstrip()))

    # You are looking for either the code or the name
    else:
        field = number_field if name.isnumeric() else name_field
        args.append((field, operator, name))

    return self.search(args, limit=limit).name_get()


class NumberName(models.AbstractModel):
    _description = "Base for tables with a number and a name"
    _name = "l10n.es.tgss.number_name"
    _order = "number, name"

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
        return smart_search(name, args, operator, limit)
