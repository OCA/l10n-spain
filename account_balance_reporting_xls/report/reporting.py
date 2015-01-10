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
_logger = logging.getLogger(__name__)

_ir_translation_name = 'account.balance.reporting.print'


class account_balance_reporting_print(report_sxw.rml_parse):

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
        self.cr.execute(
            "SELECT TO_CHAR(r.calc_date, 'DD-MM-YYYY HH24:MI:SS') AS calc_date, t.name AS tname "
            + "FROM account_balance_reporting r "
            + "INNER JOIN account_balance_reporting_template t ON r.template_id = t.id "
            + "WHERE r.id = %s ", ([self.report_id, ]))
        fields = self.cr.dictfetchall()
        # !!!!!!!!!!!!!!!!!!!!!!
        # TODO: Do not use SQL
#         fields = 

        fields = fields[0]
        return fields

    def _lines(self, object):
        
        abr_obj = self.pool.get('account.balance.reporting')
        _ = self._

#         acc_bal_rep = object[0]
#         acc_bal_rep_id = acc_bal_rep.id
 
        if self.report_design == "Generic balance report (non zero lines)":
            where_zero = "AND (l.current_value-l.previous_value) != 0 "            
        else:
            where_zero = ""
 
        select_extra, join_extra, where_extra = abr_obj._report_xls_query_extra(self.cr, self.uid, self.context)
 
        # SQL select for performance reasons, as a consequence, there are no field value translations.
        # If performance is no issue, you can adapt the _report_xls_template in an inherited module to add field value translations.
        
        self.cr.execute(
            "SELECT l.name AS name, l.code as code, l.notes AS notes, l.previous_value AS previous_value, l.current_value AS current_value, (l.current_value-l.previous_value) AS balance "
            + select_extra
            + "FROM account_balance_reporting_line l "
            + "INNER JOIN account_balance_reporting r ON l.report_id = r.id "
            + join_extra
            + "WHERE r.id = %s "
            + where_zero
            + where_extra, ([self.report_id, ]))
        lines = self.cr.dictfetchall()
        # !!!!!!!!!!!!!!!!!!!!!!
        # TODO: Do not use SQL
        # lines = 
 
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
    parser=account_balance_reporting_print, header=False)
