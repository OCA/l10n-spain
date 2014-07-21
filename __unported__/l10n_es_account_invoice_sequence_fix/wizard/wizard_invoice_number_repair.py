# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account renumber wizard
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

__author__ = "www.eficent.com"


import wizard
from openerp import netsvc
from openerp import pooler
from openerp.tools.translate import _
import time
from datetime import datetime

class wizard_invoice_number_repair(wizard.interface):
    """
    Invoice number repair wizard.
    """

    ############################################################################
    # Init form
    ############################################################################

    _init_fields = {
    }

    _init_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Repair invoice numbers">
        <label string="This wizard will help you copy the move number of an invoice to the invoice number field. Invoices should have an invoice number different to the move number." colspan="4"/>
        <label string="Attention! This wizard should only be run once, and only if invoices were created before installing module nan_account_invoice_sequence." colspan="4"/>        
        <label string="" colspan="4"/>
        <newline/>
    </form>"""

    ############################################################################
    # Renumber form/action
    ############################################################################

    _repair_fields = {
    }

    _repair_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Repair invoice numbers - Done" colspan="4">
        <group string="" colspan="4">
            <label string="The invoice numbers have been converted successfully." colspan="4"/>
            <label string="" colspan="4"/>
            <label string="You may now review them using the show results button." colspan="4"/>
        </group>
    </form>"""

    def _repair_action(self, cr, uid, data, context):
        """
        Action that repairs the invoice numbers 
        """
        logger = netsvc.Logger()

        logger.notifyChannel("l10n_es_account_invoice_sequence_fix", netsvc.LOG_DEBUG, "Searching for invoices.")

        invoice_facade = pooler.get_pool(cr.dbname).get('account.invoice')
        invoice_ids = invoice_facade.search(cr, uid, [('move_id','<>','')], limit=0, order='id', context=context)

        if len(invoice_ids) == 0:
            raise wizard.except_wizard(_('No Data Available'), _('No records found for your selection!'))

        logger.notifyChannel("l10n_es_account_invoice_sequence_fix", netsvc.LOG_DEBUG, "Repairing %d invoices." % len(invoice_ids))

        for invoice in invoice_facade.browse(cr, uid, invoice_ids):
            move_id = invoice.move_id or False
            if move_id:
                cr.execute('UPDATE account_invoice SET invoice_number=%s WHERE id=%s', (move_id.id, invoice.id))

        logger.notifyChannel("l10n_es_account_invoice_sequence_fix", netsvc.LOG_DEBUG, "%d invoices repaired." % len(invoice_ids))

        vals = {
        }
        return vals


    ############################################################################
    # Show results action
    ############################################################################

    def _show_results_action(self, cr, uid, data, context):
        """
        Action that shows the list of invoices, so the user can review
        the invoice numbers.
        """
        cr.execute('select id,name from ir_ui_view where model=%s and type=%s', ('account.invoice', 'tree'))
        view_res = cr.fetchone()
        res = {
            'domain': "[('move_id','<>','')]",
            'name': _("Repaired invoices"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'view_id': view_res,
            'context': context,
            'type': 'ir.actions.act_window',
        }
        return res


    ############################################################################
    # States
    ############################################################################

    states = {
        'init': {
            'actions': [],
            'result': {'type':'form', 'arch': _init_form, 'fields': _init_fields, 'state':[('end', 'Cancel', 'gtk-cancel', True),('repair', 'Repair', 'gtk-ok', True)]}
        },
        'repair': {
            'actions': [_repair_action],
            'result': {'type':'form', 'arch': _repair_form, 'fields': _repair_fields, 'state':[('end', 'Close', 'gtk-close', True), ('show_results', 'Show results', 'gtk-ok', True)]}
        },
        'show_results': {
            'actions': [],
            'result': {'type': 'action', 'action': _show_results_action, 'state':'end'}
        }
    }

wizard_invoice_number_repair('l10n_es_account_invoice_sequence_fix.repair_wizard')

