##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2009 Albert Cervera i Areny (http://www.nan-tic.com). All Rights Reserved
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

import mx.DateTime
from mx.DateTime import RelativeDateTime

from osv import fields, osv


class account_payment_term(osv.osv):
    _inherit="account.payment.term"

    def _check_payment_days(self, cr, uid, id, context=None):
        days = self.read(cr, uid, id, ['payment_days'], context)[0]['payment_days']
        if days == False:
            return True
        # Admit space, dash and colon separators.
        days = days.replace(' ','-').replace(',','-')
        days = days.split('-')	
        try:
            days = [int(x) for x in days]
        except:
            return False

        for day in days:
            if day <= 0 or day > 31:
                return False
        return True

    _columns={
        'payment_days':fields.char('Payment days', size=11, help="If a company has more than one payment days in a month you should fill them in this field and set 'Day of the Month' field in line to zero. For example, if a company pays the 5th and 20th days of the month you should write '5-20' here."),
    }
    _constraints = [(_check_payment_days, 'Error: Payment days field format is not valid.', ['payment_days'])]

    def compute(self, cr, uid, id, value, date_ref=False, context=None):
        result = super(account_payment_term,self).compute(cr, uid, id, value, date_ref, context)
        term = self.browse(cr, uid, id, context)
        if not term.payment_days:
            return result

        # Admit space, dash and colon separators.
        days = term.payment_days.replace(' ','-').replace(',','-')
        days = [x.strip() for x in days.split('-') if x]
        if not days:
            return result
        days = [int(x) for x in days]
        days.sort(reverse=True)
        new_result = []
        for line in result:
            new_date = None
            date = mx.DateTime.strptime( line[0], '%Y-%m-%d' )
            for day in days:
                if date.day <= day:
                    if day > date.days_in_month:
                        day = date.days_in_month
                    new_date = date + RelativeDateTime( day=day )
                    break
            if not new_date:
                day = days[0]
                if day > date.days_in_month:
                    day = date.days_in_month
                new_date = date + RelativeDateTime( day=day, months=1 )
            new_result.append( (new_date.strftime('%Y-%m-%d'), line[1]) )
        return new_result

account_payment_term()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
