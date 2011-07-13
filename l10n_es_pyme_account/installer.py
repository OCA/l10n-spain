# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010 Domatix Technologies  S.L. (http://www.domatix.com) 
#                       info <info@domatix.com>
#                        Angel Moya <angel.moya@domatix.com>
#
#        $Id$
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################


from osv import fields, osv


class account_fiscalyear(osv.osv):
    _name = "account.fiscalyear"
    _inherit = "account.fiscalyear"

    def create_period_special(self,cr, uid, ids, context=None):
        for fy in self.browse(cr, uid, ids, context=context):
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            df = datetime.strptime(fy.date_stop, '%Y-%m-%d')
            if ds.strftime('%Y') != df.strftime('%Y'):
                years=ds.strftime('%Y')+'-'+ df.strftime('%Y')
            else:
                years=ds.strftime('%Y')
            
            #Apertura
            self.pool.get('account.period').create(cr, uid, {
                    'name': 'A/'+years,
                    'code': 'A/'+years,
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': ds.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                    'special':True,
                })
            #Cierre
            self.pool.get('account.period').create(cr, uid, {
                    'name': 'C/'+years,
                    'code': 'C/'+years,
                    'date_start': df.strftime('%Y-%m-%d'),
                    'date_stop': df.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                    'special':True,
                })
            #PyG
            self.pool.get('account.period').create(cr, uid, {
                    'name': 'PG/'+years,
                    'code': 'PG/'+years,
                    'date_start': df.strftime('%Y-%m-%d'),
                    'date_stop': df.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                    'special':True,
                })
        return True

account_fiscalyear()


class account_installer(osv.osv_memory):
    _name = 'account.installer'
    _inherit = 'account.installer'
    
    
    _columns = {
                'open_close_periods':fields.boolean('Create Open/Close and PyG Periods'),   
            }
    _defaults = {
                 'open_close_periods':False,
                 }
    
    def execute(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        super(account_installer, self).execute(cr, uid, ids, context=context)
        
        fy_obj = self.pool.get('account.fiscalyear')
        
        if res.get('open_close_periods', False) and res.get('date_start', False) and res.get('date_stop', False) and res.get('company_id', False):
            f_ids = fy_obj.search(cr, uid, [('date_start', '<=', res['date_start']), ('date_stop', '>=', res['date_stop']), ('company_id', '=', res['company_id'])], context=context)
            if f_ids:
                fy_obj.create_period_special(cr, uid, [f_ids[0]])


account_installer()