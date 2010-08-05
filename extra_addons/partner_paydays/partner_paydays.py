##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 NaN Projectes de Programari Lliure, S.L.  All Rights Reserved
#                       http://www.NaN-tic.com
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from osv import fields
import datetime

class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _columns = {
        'payment_days':fields.char('Payment days', size=11, help="If a company has more than one payment days in a month you should fill them in this field and set 'Day of the Month' field in line to zero. For example, if a company pays the 5th and 20th days of the month you should write '5-20' here."),
        'pays_during_holidays': fields.boolean('Pays During Holidays', help='Indicates whether the partner pays during holidays. If it doesn''t, it will be taken into account when calculating due dates.'),
        'holiday_ids': fields.one2many('res.partner.holidays', 'partner_id', 'Holidays'),
    }
    _defaults = {
        'pays_during_holidays': lambda *a: True,
    }
res_partner()

class res_partner_holidays(osv.osv):
    _name = 'res.partner.holidays'
    _order = 'start ASC'
    _columns = {
        'partner_id' : fields.many2one('res.partner', 'Partner', required=True, ondelete='cascade' ),
        'start' : fields.date('Start', required=True),
        'end' : fields.date('End', required=True)
    }

    def name_get(self, cr, uid, ids, context=None):
        result = []
        for record in self.browse(cr, uid, ids, context):
            result.append( (record.id, '%s - %s' % (record.start, record.end) ) )
        return result

res_partner_holidays()

class account_payment_term(osv.osv):
    _inherit="account.payment.term"

    def days_in_month(self, date):
        if date.month == 12:
            return date.replace(day=31)
        date = date.replace(month=date.month+1, day=1) - datetime.timedelta(days=1)
        return date.day

    def next_day(self, date, day):
        if date.day == day:
            return date
        if day < 1:
            day = 1
        if day > self.days_in_month(date):
            day = self.days_in_month(date)
        while True:
            date += datetime.timedelta(days=1)
            if date.day == day:
                return date

    def _after_holidays(self, cr, uid, partner, date, days):
        for holidays in partner.holiday_ids:
            start = datetime.datetime.strptime( datetime.datetime.strptime(holidays.start,'%Y-%m-%d').strftime(date.strftime('%Y')+'-%m-%d'),'%Y-%m-%d' )
            end = datetime.datetime.strptime( datetime.datetime.strptime(holidays.end,'%Y-%m-%d').strftime(date.strftime('%Y')+'-%m-%d'),'%Y-%m-%d' )
            if date >= start and date <= end:
                date = end + datetime.timedelta(days=1)
            found = False
            for day in days:
                if date.day <= day:
                    date = self.next_day( date, day )
                    found = True
                    break
            if days and not found:
                date = self.next_day( date, days[0] )
        return date.strftime('%Y-%m-%d')

    def compute(self, cr, uid, id, value, date_ref=False, context=None):
        if context is None:
            context = {}

        result = super(account_payment_term,self).compute(cr, uid, id, value, date_ref, context)
        if not context.get('partner_id'):
            return result
        partner = self.pool.get('res.partner').browse(cr, uid, context.get('partner_id'), context)

        # Admit space, dash and colon separators.
        days = (partner.payment_days or '').replace(' ','-').replace(',','-')
        days = [x.strip() for x in days.split('-') if x]
        days = [int(x) for x in days]
        days.sort()

        new_result = []
        for line in result:
            date = datetime.datetime.strptime( line[0], '%Y-%m-%d' )

            # dias fijos
            for day in days:
                if date.day <= day:
                    date = self.next_day( date, day )
                    break

            if not partner.pays_during_holidays:
                date = self._after_holidays(cr, uid, partner, date, days)

            new_result.append( (date, line[1]) )

        return new_result



account_payment_term()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
