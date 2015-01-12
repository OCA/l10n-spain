# -*- coding: utf-8 -*-
################################################################
#    License, author and contributors information in:          #
#    __openerp__.py file at the root folder of this module.    #
################################################################

from osv import fields, osv
import pooler
import logging
_logger = logging.getLogger(__name__)
from openerp.osv import orm


class print_wizard(osv.osv_memory):
    _inherit = 'account.balance.reporting.print.wizard'
    
    def xls_export(self, cr, uid, ids, context=None):
        return self.print_report(cr, uid, ids, context=context)

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        
        data = self.read(cr,uid,ids)[-1]

        datas = {
            'report_id': data.get('report_id') and data['report_id'][0] or None,
            'report_name': data.get('report_id') and data['report_id'][1] or None,
            'report_design': data.get('report_xml_id') and data['report_xml_id'][1] or None,
            'ids': context.get('active_ids', []),
            'model':'account.balance.reporting',
            'form': data,
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
                if context.get('xls_export'):
                    return {
                        'type': 'ir.actions.report.xml',
                        'report_name': 'reporting.xls',
                        'datas': datas,
                    }
                else:
                    return {
                        'type': 'ir.actions.report.xml',
                        'report_name': report_xml.report_name,
                        'datas': datas,
                    }
        return { 'type': 'ir.actions.act_window_close' }
                 
print_wizard()
