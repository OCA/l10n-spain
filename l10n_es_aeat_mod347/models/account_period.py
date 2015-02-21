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
from openerp.osv import fields, orm
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountPeriod(orm.Model):
    _inherit = "account.period"

    def assign_quarter(self, cr, uid, ids, context=None):
        quarters = self._columns['quarter'].selection
        for period in self.browse(cr, uid, ids, context):
            ds = datetime.strptime(period.date_start,
                                   DEFAULT_SERVER_DATE_FORMAT)
            quarter = quarters[(ds.month-1)/3][0]
            self.write(cr, uid, period.id, {'quarter': quarter}, context)
        return True

    _columns = {
        'quarter': fields.selection([('first', 'First'),
                                     ('second', 'Second'),
                                     ('third', 'Third'),
                                     ('fourth', 'Fourth')], 'Quarter'),
    }


class account_fiscalyear(orm.Model):
    _inherit = "account.fiscalyear"

    def create_period(self, cr, uid, ids, context=None, interval=1):
        period_obj = self.pool.get('account.period')
        period_ids = set(period_obj.search(cr, uid, [], context=context))
        super(account_fiscalyear, self).create_period(
            cr, uid, ids, context, interval)
        new_period_ids = set(period_obj.search(cr, uid, [], context=context))
        new_period_ids = list(new_period_ids - period_ids)
        period_obj.assign_quarter(cr, uid, new_period_ids, context)
        return True
