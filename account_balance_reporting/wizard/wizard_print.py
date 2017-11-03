# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account balance reporting engine
#    Copyright (C) 2009 Pexego Sistemas Informáticos. All Rights Reserved
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

"""
Account balance report print wizard
"""
__author__ = "Borja López Soilán (Pexego)"


from osv import fields, osv
import pooler


class print_wizard(osv.osv_memory):
    _name='account.balance.reporting.print.wizard'
    
    def _get_current_report_id(self, cr, uid, ctx):   
        rpt_facade = pooler.get_pool(cr.dbname).get('account.balance.reporting')
        report_id = None
        if ctx.get('active_model') == 'account.balance.reporting' and ctx.get('active_ids') and ctx.get('active_ids')[0]:
            report_id = ctx.get('active_ids')[0]
            report_ids = rpt_facade.search(cr, uid, [('id', '=', report_id)])
            report_id = report_ids and report_ids[0] or None
        return report_id

    def _get_current_report_xml_id(self, cr, uid, ctx):
        report_id = self._get_current_report_id(cr, uid, ctx)
        rpt_facade = pooler.get_pool(cr.dbname).get('account.balance.reporting')
        report = rpt_facade.browse(cr, uid, [report_id])[0]
        report_xml_id = None
        if report.template_id and report.template_id.report_xml_id:
            report_xml_id = report.template_id.report_xml_id.id
        return report_xml_id

    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr,uid,ids)[-1]
        #rpt_facade_lines = pooler.get_pool(cr.dbname).get('account.balance.reporting.line')
        #var = data.get('report_id') and data['report_id'][0] or None
        #report_lines_ids = rpt_facade_lines.search(cr, uid, [('report_id', '=', var)])
        #print data
        #print str(data.get('report_id'))
        #print str(data['report_id'][0])
        datas ={
                'ids': [data.get('report_id') and data['report_id'][0] or None],
                'model':'account.balance.reporting',
                'form': data
                }
        rpt_facade = pooler.get_pool(cr.dbname).get('ir.actions.report.xml')
        report_xml = None
        if data.get('report_xml_id'):
            report_xml_id = data['report_xml_id']
            report_xml_ids = rpt_facade.search(cr, uid, [('id', '=', report_xml_id[0])])
            report_xml_id = report_xml_ids and report_xml_ids[0] or None
            if report_xml_id:
                report_xml = rpt_facade.browse(cr, uid, [report_xml_id])[0]
            if report_xml:
                return {
                    'type' : 'ir.actions.report.xml',
                    'report_name' : report_xml.report_name,
                    'datas' : datas #{'ids': [data.get('report_id') and data['report_id'][0] or None]},
                }
        return { 'type': 'ir.actions.act_window_close' }
        
    _columns = {
        'report_id' : fields.many2one('account.balance.reporting', "Report"),
        'report_xml_id': fields.many2one('ir.actions.report.xml', "Design"),
    }
    
    _defaults = {
        'report_id': _get_current_report_id,
        'report_xml_id': _get_current_report_xml_id
    }

print_wizard()

