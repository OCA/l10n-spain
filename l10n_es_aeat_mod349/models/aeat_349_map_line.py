# -*- coding: utf-8 -*-
# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class Aeat349MapLines(models.Model):
    _name = 'aeat.349.map.line'
    _description = 'Aeat 349 Map Line'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name')
    physical_product = fields.Boolean(string='Involves physical product')
    taxes = fields.One2many(
        comodel_name='account.tax.template',
        inverse_name='aeat_349_operation_key',
        string="Taxes")

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for line in self:
            name = line.code + ' ' + line.name
            result.append((line.id, name))
        return result
