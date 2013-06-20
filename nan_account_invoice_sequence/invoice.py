# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L. All Rights Reserved.
#                    http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import netsvc
from osv import osv
from osv import fields
from tools.translate import _
import psycopg2

class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def _number(self, cr, uid, ids, name, args, context=None):
        result = {}
        for invoice in self.browse(cr, uid, ids, args):
            result[invoice.id] = invoice.invoice_number
        return result

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'invoice_number' : False,            
        })
        return super(account_invoice, self).copy(cr, uid, id, default, context=context)   

    # TODO: Due to bug #704922 in OpenERP server we create a new 'invoice_number' field and make 'number' a function field.
    # The bug doesn't prevent inheritance of function fields (or related) to work (not 100% well, but they work) whereas
    # trying to make 'number' a char would crash when trying to validate the invoice. Even if a patch was provided, by 
    # now, we'll keep this compatible with current server version.
    _columns = {
        'number': fields.function(_number, method=True, type='char', size=32, string='Invoice Number', store=True, help='Unique number of the invoice, computed automatically when the invoice is created.'),
        #'number': fields.char('Invoice Number', size=32, readonly=True, help="Unique number of the invoice, computed automatically when the invoice is created."),
        'invoice_number': fields.char('Invoice Number', size=32, readonly=True, help="Unique number of the invoice, computed automatically when the invoice is created."),
    }
    def action_number(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for invoice in self.browse(cr, uid, ids, context):
            if invoice.invoice_number:
                continue
            sequence = invoice.journal_id.invoice_sequence_id
            if not sequence:
                raise osv.except_osv(_('Error!'), _('Journal %s has no sequence defined for invoices.') % invoice.journal_id.name)

            ctx = context.copy()
            ctx['fiscalyear_id'] = self.pool.get('account.period').browse(cr, uid, invoice.period_id.id).fiscalyear_id.id
            number = self.pool.get('ir.sequence').get_id(cr, uid, sequence.id, context=ctx)
            
            self.write(cr, uid, [invoice.id], {
                #'number': number,
                'invoice_number': number,
            }, context)
        result = super(account_invoice, self).action_number(cr, uid, ids, context)

        # As super's action_number() will store internal_number we clear it afterwards. The reason is that post() function
        # in account.move will try to use this 'internal_number' if move is created again. As this module makes 'number'
        # no longer handler account.move number we must ensure the system does not try to reuse it if invoice is cancelled
        # and opened again.
        #
        # We could also have overriden account.move's 'post()' function, but this seems cleaner/less intrusive because we 
        # must override action_number() anyway.
        self.write(cr, uid, ids, {
            'internal_number': False,
        }, context)
        return result

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

