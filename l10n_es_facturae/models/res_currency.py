# -*- coding: utf-8 -*-
# © 2017 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    def get_current_rate(self):
        date = self._context.get('date') or fields.Datetime.now()
        company_id = self._context.get(
            'company_id') or self.env['res.users']._get_company().id
        rate = self.env['res.currency.rate'].search(
            [
                ('currency_id', '=', self.id),
                ('company_id', '=', company_id),
                ('name', '<=', date)
            ],
            order='name desc', limit=1
        )
        if rate:
            return rate.ensure_one()
        rate = self.env['res.currency.rate'].search(
            [
                ('currency_id', '=', self.id),
                ('company_id', '=', False),
                ('name', '<=', date)
            ],
            order='name desc', limit=1
        )
        if rate:
            return rate.ensure_one()
        return False
