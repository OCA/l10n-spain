# -*- encoding: utf-8 -*-

from odoo import _, api, fields, models, exceptions
from odoo.exceptions import UserError, ValidationError


class L10nEsAeatMapTax(models.Model):
    _inherit = 'l10n.es.aeat.map.tax'

    # map_parent_id = fields.Many2one(ondelete='cascade')

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if self.env.context.get('from_init_hook_180', False):
            default['model'] = 180
        return super().copy(default)

    @api.constrains('date_from', 'date_to', 'model')
    def _unique_date_range(self):
        for map in self:
            domain = [('id', '!=', map.id), ('model', '=', map.model)]
            if map.date_from and map.date_to:
                domain += ['|', '&',
                           ('date_from', '<=', map.date_to),
                           ('date_from', '>=', map.date_from),
                           '|', '&',
                           ('date_to', '<=', map.date_to),
                           ('date_to', '>=', map.date_from),
                           '|', '&',
                           ('date_from', '=', False),
                           ('date_to', '>=', map.date_from),
                           '|', '&',
                           ('date_to', '=', False),
                           ('date_from', '<=', map.date_to),
                           ]
            elif map.date_from:
                domain += [('date_to', '>=', map.date_from)]
            elif map.date_to:
                domain += [('date_from', '<=', map.date_to)]
            date_lst = map.search(domain)
            if date_lst:
                raise exceptions.Warning(
                    _("Error! Las fechas de los registros se solapan con un registro existente.")
                )

