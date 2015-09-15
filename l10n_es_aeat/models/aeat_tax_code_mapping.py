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
    map_lines = fields.One2many(
        comodel_name='aeat.mod.map.tax.code.line',
        inverse_name='map_parent_id', string="Map lines", required=True)
    model = fields.Integer(string="AEAT Model", required=True)

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


class AeatModMapTaxCodeLine(models.Model):
    _name = 'aeat.mod.map.tax.code.line'

    field_number = fields.Integer(string="Field number", required=True)
    tax_codes = fields.Many2many(
        comodel_name='account.tax.code.template', string="Tax codes",
        required=True)
    name = fields.Char(required=True)
    map_parent_id = fields.Many2one('aeat.mod.map.tax.code', required=True)
    to_regularize = fields.Boolean()

    def get_taxes_amount(self, report, periods):
        tax_amount = 0
        for tax_code in self.tax_codes:
            move_lines = report._get_tax_code_lines(tax_code, periods=periods)
            tax_amount += sum([x.tax_amount for x in move_lines])
        return tax_amount
