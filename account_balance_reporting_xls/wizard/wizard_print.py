# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp.osv import orm


class PrintWizard(orm.TransientModel):
    _inherit = 'account.balance.reporting.print.wizard'

    def xls_export(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids[0], context=context)
        datas = {
            'report_id': (data.get('report_id') and
                          data['report_id'][0] or None),
            'report_name': (data.get('report_id') and
                            data['report_id'][1] or None),
            'report_design': (data.get('report_xml_id') and
                              data['report_xml_id'][1] or None),
            'ids': context.get('active_ids', []),
            'model': 'account.balance.reporting',
            'form': data,
        }
        rpt_facade = self.pool['ir.actions.report.xml']
        report_xml = None
        if data.get('report_xml_id'):
            report_xml_id = data['report_xml_id']
            report_xml_ids = rpt_facade.search(
                cr, uid, [('id', '=', report_xml_id[0])], context=context)
            report_xml_id = report_xml_ids and report_xml_ids[0] or None
            if report_xml_id:
                report_xml = rpt_facade.browse(
                    cr, uid, [report_xml_id], context=context)[0]
            if report_xml:
                return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'reporting.xls',
                    'datas': datas,
                }
        return True
