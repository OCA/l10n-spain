# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.report import report_sxw
from openerp.tools.translate import translate, _
import logging

_ir_translation_name = 'account.balance.reporting.print'


class account_balance_reporting_print(report_sxw.rml_parse):

    _logger = logging.getLogger(__name__)
    def set_context(self, objects, data, ids, report_type=None):
        super(account_balance_reporting_print, self).set_context(objects, data,
                                                                 ids)
        abr_obj = self.pool.get('account.balance.reporting')
        self.report_type = report_type
        self.report_id = data['report_id']
        self.report_name = data['report_name']
        self.report_design = data['report_design']
        self.localcontext.update({
           'additional_data': self._get_additional_data(),
        })

    def __init__(self, cr, uid, name, context):
        if context is None:
            context = {}

        super(account_balance_reporting_print, self).__init__(cr, uid, name,
                                                              context=context)
        self.localcontext.update({
            'time': time,
            'lines': self._lines,
            '_': self._,
        })
        self.context = context

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(self.cr, _ir_translation_name, 'report', lang,
                         src) or src

    def _get_additional_data(self):
        abr_obj = self.pool.get('account.balance.reporting')
        abr = abr_obj.browse(self.cr, self.uid,
                             self.report_id, self.context)
        calc_date = abr and abr.calc_date or False
        tname = abr and abr.template_id and abr.template_id.name or False
        fields = {'calc_date': calc_date,
                  'tname': tname,}
        return fields

    def _lines(self, object):
        _ = self._
        # abr stands for 'account balance report'
        abr = object
#         abr = abr_obj.browse(self.cr, self.uid, self.report_id, self.context)
        non_zero_name = "Generic balance report (non zero lines)"
        non_zero = (self.report_design == non_zero_name)
        # No SQL is used, as performance should not be a problem using
        # already calculated values.        
        lines = []
        abr_line_ids = abr.line_ids
        for line in abr_line_ids:
#             line_balance = line.previous_value and \
#                             (line.current_value - line.previous_value) or False
            line_balance = (line.current_value - line.previous_value)
            if non_zero and abs(line_balance)<0.005:
                continue
            notes = line.notes and line.notes.encode('utf-8') or ''
            line_fields = {'code': line.code,
                           'name': line.name,
                           'previous_value': line.previous_value,
                           'current_value': line.current_value,
                           'balance': line_balance,
                           'notes': line.notes,
                           }
            lines.append(line_fields)
        return lines
    
#         def formatLang(self, value, digits=None, date=False, date_time=False,
#                        grouping=True, monetary=False, dp=False,
#                        currency_obj=False):
#             if isinstance(value, (float, int)) and not value:
#                 return ''
#             else:
#                 return super(account_balance_reporting_print,
#                              self).formatLang(value, digits, date, date_time,
#                                               grouping, monetary, dp,
#                                               currency_obj)

report_sxw.report_sxw('report.account.balance.reporting.print',
                      'account.balance.reporting',
                      parser=account_balance_reporting_print,
                      header=False)
