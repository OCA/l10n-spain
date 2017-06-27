# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class AeatSiiPaymentModeKey(models.Model):
    _name = 'aeat.sii.payment.mode.key'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name')

    @api.multi
    def name_get(self):
        vals = []
        for record in self:
            name = u'[{}]-{}'.format(record.code, record.name)
            vals.append(tuple([record.id, name]))
        return vals


class PaymentMode(models.Model):
    _inherit = 'payment.mode'

    sii_key = fields.Many2one(
        comodel_name='aeat.sii.payment.mode.key',
        string="SII key", required=True)
