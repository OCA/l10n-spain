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
from openerp import fields, api, models


class AccountPeriod(models.Model):
    _inherit = "account.period"

    @api.multi
    def assign_quarter(self):
        quarters = self._fields['quarter'].selection
        for period in self:
            ds = fields.Date.from_string(period.date_start)
            period.quarter = quarters[(ds.month - 1)/3][0]
        return True

    quarter = fields.Selection(
        [('first', 'First'),
         ('second', 'Second'),
         ('third', 'Third'),
         ('fourth', 'Fourth')], 'Quarter')


class AccountFiscalyear(models.Model):
    _inherit = "account.fiscalyear"

    @api.multi
    def create_period3(self):
        return self.create_period(interval=3)

    @api.v7
    def create_period(self, cr, uid, ids, context=None, interval=1):
        recs = self.browse(cr, uid, ids, context=context)
        recs.create_period(interval=interval)

    @api.v8
    def create_period(self, interval=1):
        period_obj = self.env['account.period']
        periods_before = period_obj.search([])
        super(AccountFiscalyear, self).create_period(interval=interval)
        periods_after = period_obj.search([])
        new_periods = periods_after - periods_before
        new_periods.assign_quarter()
        return True
