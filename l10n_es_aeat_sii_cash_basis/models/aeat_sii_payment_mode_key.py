# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AeatSiiPaymentModeKey(models.Model):
    _name = 'aeat.sii.payment.mode.key'

    code = fields.Char(required=True)
    name = fields.Char(translate=True)

    def name_get(self):
        vals = []
        for record in self:
            name = u'[%s]-%s' % (record.code, record.name)
            vals.append(tuple([record.id, name]))
        return vals
