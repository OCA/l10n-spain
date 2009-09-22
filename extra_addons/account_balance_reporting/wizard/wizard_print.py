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


import wizard
import pooler


class wizard_print(wizard.interface):
    """
    Account balance report print wizard.
    Allows the user to select which 'balance report' will be printed,
    and which printing template will be used. By default the current
    balance report and its template printing design will be used.
    """

    init_fields = {
        'report_id' : {'type':'many2one', 'relation': 'account.balance.report', 'required': True},
        'report_xml_id' : {'type':'many2one', 'relation': 'ir.actions.report.xml', 'required': True},
    }


    init_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Print report" colspan="4">
        <field string="Report data" name="report_id"/>
        <newline/>
        <field string="Report design" name="report_xml_id" domain="[('model','=','account.balance.report')]"/>
    </form>"""


    def _init_action(self, cr, uid, data, context):
        """
        Gets the currently selected balance report to use it as the
        default value for the wizard form.
        """
        rpt_facade = pooler.get_pool(cr.dbname).get('account.balance.report')
        report_id = None
        report_xml_id = None
        if data.get('model') == 'account.balance.report':
            report_id = data.get('id')
            report_ids = rpt_facade.search(cr, uid, [('id', '=', report_id)])
            report_id = report_ids and report_ids[0] or None
            if report_id:
                report = rpt_facade.browse(cr, uid, [report_id])[0]
                if report.template_id and report.template_id.report_xml_id:
                    report_xml_id = report.template_id.report_xml_id.id
        return { 'report_id' : report_id, 'report_xml_id' : report_xml_id,  }


    def _print_action(self, cr, uid, data, context):
        """
        Sets the printing template (as selected by the user) before printing.
        """
        rpt_facade = pooler.get_pool(cr.dbname).get('ir.actions.report.xml')

        if data['form'].get('report_xml_id'):
            report_xml_id = data['form']['report_xml_id']
            report_xml_ids = rpt_facade.search(cr, uid, [('id', '=', report_xml_id)])
            report_xml_id = report_xml_ids and report_xml_ids[0] or None
            if report_xml_id:
                report_xml = rpt_facade.browse(cr, uid, [report_xml_id])[0]
                self.states['print']['result']['report'] = report_xml.report_name

        return { }

    states = {
        'init': {
            'actions': [_init_action],
            'result': {'type':'form', 'arch': init_form, 'fields': init_fields, 'state':[('end','Cancel'),('print','Print')]}
        },
        'print': {
            'actions': [_print_action],
            'result': {'type':'print', 'report': 'NOTFOUND', 'state':'end'}
        }
    }
wizard_print('account_balance_report.print_wizard')

