# -*- encoding: utf-8 -*-
##############################################################################
#
#    Avanzosc - Avanced Open Source Consulting
#    Copyright (C) 2010 - 2011 Avanzosc <http://www.avanzosc.com>
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from osv import osv
from osv import fields

class account_find_analytic_entries(osv.osv_memory):
    _name = 'account.find.analytic.entries'
    _description = 'Find Analytic Entries'
    
    def _get_default_invoice_type(self, cr, uid, context=None):
        factor = self.pool.get('hr_timesheet_invoice.factor')
        return factor.search(cr, uid, [])[0]
 
    _columns = {
       'start_date': fields.date('Start Date', required=True),
       'finish_date': fields.date('Finish Date', required=True),
       'invoice_type': fields.many2one('hr_timesheet_invoice.factor','Invoice Type', required=True),
    }
    
    _defaults = {
        'invoice_type': lambda self, cr, uid, context: self._get_default_invoice_type(cr, uid, context),
    }
    
    def action_find(self, cr, uid, ids, context=None):
        for entri in self.browse(cr, uid, ids):
            wizard = {
                'type': 'ir.actions.act_window',
                'res_model': 'account.analytic.line',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'domain': [('date', '>=', entri.start_date), ('date', '<=', entri.finish_date), ('to_invoice', '=', entri.invoice_type.id), ('invoice_id', '=', False)],
                'context':context
            }
            return wizard
        return False
    
account_find_analytic_entries()