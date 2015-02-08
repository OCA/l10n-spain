# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2009 Pexego Sistemas Informáticos.
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
from openerp.osv import orm, fields


class PrintWizard(orm.TransientModel):
    _name = 'account.balance.reporting.print.wizard'

    def _get_current_report_id(self, cr, uid, context=None):
        if context is None:
            context = {}  # Ensuring a dict.
        rpt_facade = self.pool['account.balance.reporting']
        report_id = None
        if (context.get('active_model') == 'account.balance.reporting' and
                context.get('active_ids') and context.get('active_ids')[0]):
            report_id = context.get('active_ids')[0]
            report_ids = rpt_facade.search(cr, uid, [('id', '=', report_id)])
            report_id = report_ids and report_ids[0] or None
        return report_id

    def _get_current_report_xml_id(self, cr, uid, context=None):
        if context is None:
            context = {}  # Ensuring a dict.
        report_id = self._get_current_report_id(cr, uid, context=context)
        rpt_facade = self.pool['account.balance.reporting']
        report = rpt_facade.browse(cr, uid, [report_id])[0]
        report_xml_id = None
        if report.template_id and report.template_id.report_xml_id:
            report_xml_id = report.template_id.report_xml_id.id
        return report_xml_id

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}  # Ensuring a dict.
        data = self.read(cr, uid, ids)[-1]
        datas = {
            'ids': [data.get('report_id') and data['report_id'][0] or None],
            'model': 'account.balance.reporting',
            'form': data
        }
        rpt_facade = self.pool['ir.actions.report.xml']
        report_xml = None
        if data.get('report_xml_id'):
            report_xml_id = data['report_xml_id']
            report_xml_ids = rpt_facade.search(cr, uid,
                                               [('id', '=', report_xml_id[0])],
                                               context=context)
            report_xml_id = report_xml_ids and report_xml_ids[0] or None
            if report_xml_id:
                report_xml = rpt_facade.browse(cr, uid, [report_xml_id],
                                               context=context)[0]
            if report_xml:
                return {
                    'type': 'ir.actions.report.xml',
                    'report_name': report_xml.report_name,
                    'datas': datas
                }
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'report_id': fields.many2one('account.balance.reporting', "Report"),
        'report_xml_id': fields.many2one('ir.actions.report.xml', "Design"),
    }

    _defaults = {
        'report_id': _get_current_report_id,
        'report_xml_id': _get_current_report_xml_id
    }
