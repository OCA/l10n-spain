# -*- coding: utf-8 -*-
##############################################################################
#
#    account_balance_reporting module for OpenERP,


#    Copyright (C) 2011 SYLEAM Info Services (<http://www.syleam.fr/>)
#              Jean-Sébastien SUZANNE <jean-sebastien.suzanne@syleam.fr>
#
#    This file is a part of account_balance_reporting
#
#    account_balance_reporting is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    account_balance_reporting is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import netsvc
logger = netsvc.Logger()

def migrate(cr, v):
    """
    old name of balance report is account.balance.report
    or this name is also use by a osv_memory in v6.0
    we have replaced the name by the name of the module account.balance.reporting
    change also the name in ir.model.data and ir.model
    """
    # change name of the table
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'change name of table account_balance_report => account_balance_reporting')
    cr.execute('ALTER TABLE account_balance_report RENAME TO account_balance_reporting')
    cr.execute('ALTER TABLE account_balance_report_id_seq  RENAME TO account_balance_reporting_id_seq')
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'change name of table account_balance_report_line => account_balance_reporting_line')
    cr.execute('ALTER TABLE account_balance_report_line RENAME TO account_balance_reporting_line')
    cr.execute('ALTER TABLE account_balance_report_line_id_seq  RENAME TO account_balance_reporting_line_id_seq')
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'change name of table account_balance_report_template => account_balance_reporting_template')
    cr.execute('ALTER TABLE account_balance_report_template RENAME TO account_balance_reporting_template')
    cr.execute('ALTER TABLE account_balance_report_template_id_seq  RENAME TO account_balance_reporting_template_id_seq')
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'change name of table account_balance_report_template_line => account_balance_reporting_template_line')
    cr.execute('ALTER TABLE account_balance_report_template_line RENAME TO account_balance_reporting_template_line')
    cr.execute('ALTER TABLE account_balance_report_template_line_id_seq  RENAME TO account_balance_reporting_template_line_id_seq')
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'change name of table account_balance_report_account_period_current_rel => account_balance_reporting_account_period_current_rel')
    cr.execute('ALTER TABLE account_balance_report_account_period_current_rel RENAME TO account_balance_reporting_account_period_current_rel')
    cr.execute('ALTER TABLE account_balance_reporting_account_period_current_rel RENAME COLUMN account_balance_report_id TO account_balance_reporting_id')
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'change name of table account_balance_report_account_period_previous_rel => account_balance_reporting_account_period_previous_rel ')
    cr.execute('ALTER TABLE account_balance_report_account_period_previous_rel RENAME TO account_balance_reporting_account_period_previous_rel ')
    cr.execute('ALTER TABLE account_balance_reporting_account_period_previous_rel RENAME COLUMN account_balance_report_id TO account_balance_reporting_id')
    # change ir model data
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'change name of model in ir.model.data account_balance_report => account_balance_reporting')
    cr.execute("UPDATE ir_model_data SET name='model_account_balance_reporting' WHERE module='account_balance_reporting' AND name='model_account_balance_report'")
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'change name of model in ir.model.data account_balance_report_line => account_balance_reporting_line')
    cr.execute("UPDATE ir_model_data SET name='model_account_balance_reporting_line' WHERE module='account_balance_reporting' AND name='model_account_balance_report_line'")
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'change name of model in ir.model.data account_balance_report_template => account_balance_reporting_template')
    cr.execute("UPDATE ir_model_data SET name='model_account_balance_reporting_template' WHERE module='account_balance_reporting' AND name='model_account_balance_report_template'")
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'change name of model in ir.model.data account_balance_report_template_line => account_balance_reporting_template_line')
    cr.execute("UPDATE ir_model_data SET name='model_account_balance_reporting_template_line' WHERE module='account_balance_reporting' AND name='model_account_balance_report_template_line'")
    # change ir_model
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'change name of model in ir.model account_balance_report_line => account_balance_reporting_line')
    cr.execute("UPDATE ir_model SET name='account.balance.reporting.line', model='account.balance.reporting.line' WHERE name='account.balance.report.line'")
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'change name of model in ir.model account_balance_report_template => account_balance_reporting_template')
    cr.execute("UPDATE ir_model SET name='account.balance.reporting.template', model='account.balance.reporting.template' WHERE name='account.balance.report.template'")
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'change name of model in ir.model account_balance_report_template_line => account_balance_reporting_template_line')
    cr.execute("UPDATE ir_model SET name='account.balance.reporting.template.line', model='account.balance.reporting.template.line' WHERE name='account.balance.report.template.line'")

    cr.commit()
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'All tables was renamed')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
