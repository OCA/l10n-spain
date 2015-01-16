# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp.osv import orm


class account_balance_reporting(orm.Model):
    _inherit = "account.balance.reporting"

    # allow inherited modules to add document references
    def _report_xls_document_extra(self, cr, uid, context):
        return "''"

    def _report_xls_fields(self, cr, uid, context=None):
        # Add here the fields to show in the XLS file
        res = [
            'name',  # account.balance.reporting.line, name
            'code',
            'notes',
            'previous_value',
            'current_value',
            'balance',
        ]
        return res

    # Change/Add Template entries
    def _report_xls_template(self, cr, uid, context=None):
        return {}
