# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields, _
from openerp import exceptions


class AeatSiiMap(models.Model):
    _name = 'aeat.sii.map'
    _description = 'Aeat SII Map'

    @api.one
    @api.constrains('date_from', 'date_to')
    def _unique_date_range(self):
        # Based in l10n_es_aeat module
        domain = [('id', '!=', self.id)]
        if self.date_from and self.date_to:
            domain += ['|', '&',
                       ('date_from', '<=', self.date_to),
                       ('date_from', '>=', self.date_from),
                       '|', '&',
                       ('date_to', '<=', self.date_to),
                       ('date_to', '>=', self.date_from),
                       '|', '&',
                       ('date_from', '=', False),
                       ('date_to', '>=', self.date_from),
                       '|', '&',
                       ('date_to', '=', False),
                       ('date_from', '<=', self.date_to),
                       ]
        elif self.date_from:
            domain += [('date_to', '>=', self.date_from)]
        elif self.date_to:
            domain += [('date_from', '<=', self.date_to)]
        date_lst = self.search(domain)
        if date_lst:
            raise exceptions.Warning(
                _("Error! The dates of the record overlap with an existing "
                  "record."))

    name = fields.Char(string='Model', required=True)
    date_from = fields.Date(string='Date from')
    date_to = fields.Date(string='Date to')
    map_lines = fields.One2many(
        comodel_name='aeat.sii.map.lines',
        inverse_name='sii_map_id',
        string='Lines')


class AeatSiiMapLines(models.Model):
    _name = 'aeat.sii.map.lines'
    _description = 'Aeat SII Map Lines'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name')
    taxes = fields.Many2many(
        comodel_name='account.tax.template', string="Taxes")
    sii_map_id = fields.Many2one(
        comodel_name='aeat.sii.map',
        string='Aeat SII Map',
        ondelete='cascade')
