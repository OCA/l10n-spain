# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp.osv import orm


class AccountBalanceReporting(orm.Model):
    _inherit = "account.balance.reporting"

    def _report_xls_document_extra(self, cr, uid, context):
        """Inherit this for adding/changing document references.
        """
        return ""

    def _report_xls_fields(self, cr, uid, context=None):
        """Inherit this for adding/changing fields to export to XLS file.
        """
        return [
            'name',  # account.balance.reporting.line, name
            'code',
            'notes',
            'previous_value',
            'current_value',
            'balance',
        ]

    def _report_xls_template(self, cr, uid, context=None):
        """Inherit this for adding/changing template entries.
        """
        return {}
