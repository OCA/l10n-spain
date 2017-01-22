# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2014-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from openerp import models, fields, api, exceptions, _


class L10nEsAeatMapTax(models.Model):
    _name = 'l10n.es.aeat.map.tax'

    date_from = fields.Date(string="From Date")
    date_to = fields.Date(string="To Date")
    map_line_ids = fields.One2many(
        comodel_name='l10n.es.aeat.map.tax.line',
        inverse_name='map_parent_id', string="Map lines", required=True)
    model = fields.Integer(string="AEAT Model", required=True)

    @api.multi
    @api.constrains('date_from', 'date_to')
    def _unique_date_range(self):
        for map in self:
            domain = [('id', '!=', map.id)]
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
                    _("Error! The dates of the record overlap with an "
                      "existing record.")
                )

    @api.multi
    def name_get(self):
        vals = []
        for record in self:
            name = "%s" % record.model
            if record.date_from or record.date_to:
                name += " (%s-%s)" % (
                    record.date_from and
                    fields.Date.from_string(record.date_from) or '',
                    record.date_to and
                    fields.Date.from_string(record.date_to) or '')
            vals.append(tuple([record.id, name]))
        return vals
