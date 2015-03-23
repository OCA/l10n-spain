# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, exceptions, _


class AeatModMapTaxCode(models.Model):
    _name = 'aeat.mod.map.tax.code'

    date_from = fields.Date(string="From Date")
    date_to = fields.Date(string="To Date")
    map_lines = fields.One2many('aeat.mod.map.tax.code.line', 'map_parent_id',
                                string="Map lines")
    model = fields.Char("Aeat Model", size=3)

    @api.one
    @api.constrains('date_from', 'date_to')
    def _unique_date_range(self):
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


class AeatModMapTaxCodeLine(models.Model):
    _name = 'aeat.mod.map.tax.code.line'

    field_number = fields.Integer(string="Field number")
    tax_code = fields.Many2one('account.tax.code.template', string="Tax code")
    map_parent_id = fields.Many2one('aeat.mod.map.tax.code')

    @api.multi
    def name_get(self):
        vals = []
        for record in self:
            name = "Field: " + str(record.field_number) + '   Code: ' + \
                str(record.tax_code.code)
            vals.append(tuple([record.id, name]))
        return vals
