# -*- encoding: utf-8 -*-
from odoo import _, api, models, exceptions


class L10nEsAeatMapTax(models.Model):
    _inherit = 'l10n.es.aeat.map.tax'

    # map_parent_id = fields.Many2one(ondelete='cascade')

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if self.env.context.get('from_init_hook_180', False):
            default['model'] = 180
        return super().copy(default)

    @api.multi
    @api.constrains('date_from', 'date_to', 'model')
    def _unique_date_range(self):
        for map_tax in self:
            domain = [('id', '!=', map_tax.id), ('model', '=', map_tax.model)]
            if map_tax.date_from and map_tax.date_to:
                domain += ['|', '&',
                           ('date_from', '<=', map_tax.date_to),
                           ('date_from', '>=', map_tax.date_from),
                           '|', '&',
                           ('date_to', '<=', map_tax.date_to),
                           ('date_to', '>=', map_tax.date_from),
                           '|', '&',
                           ('date_from', '=', False),
                           ('date_to', '>=', map_tax.date_from),
                           '|', '&',
                           ('date_to', '=', False),
                           ('date_from', '<=', map_tax.date_to),
                           ]
            elif map_tax.date_from:
                domain += [('date_to', '>=', map_tax.date_from)]
            elif map_tax.date_to:
                domain += [('date_from', '<=', map_tax.date_to)]
            date_lst = map_tax.search(domain)
            if date_lst:
                raise exceptions.Warning(
                    _("Error! Las fechas de los registros se "
                      "solapan con un registro existente.")
                )
