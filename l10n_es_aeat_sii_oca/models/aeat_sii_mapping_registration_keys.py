# -*- coding: utf-8 -*-
# Copyright 2017 MINORISA (http://www.minorisa.net)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AeatSiiMappingRegistrationKeys(models.Model):
    _name = 'aeat.sii.mapping.registration.keys'
    _description = 'Aeat SII Invoice Registration Keys'

    code = fields.Char(string='Code', required=True, size=2)
    name = fields.Char(string='Name', required=True)
    type = fields.Selection(
        selection=[('sale', 'Sale'), ('purchase', 'Purchase')], string='Type',
        required=True)

    @api.multi
    def name_get(self):
        vals = []
        for record in self:
            name = u'[{}]-{}'.format(record.code, record.name)
            vals.append(tuple([record.id, name]))
        return vals
