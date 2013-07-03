# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L. All Rights Reserved.
#                    http://www.NaN-tic.com
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
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

    _columns = {
        'number': fields.char('Invoice Number', size=32, readonly=True, help="Unique number of the invoice, computed automatically when the invoice is created."),
    }
    def action_number(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for invoice in self.browse(cr, uid, ids, context):
            if invoice.number:
                continue
            sequence = invoice.journal_id.invoice_sequence_id
            if not sequence:
                raise osv.except_osv(_('Error!'), _('Journal %s has no sequence defined for invoices.') % invoice.journal_id.name)

            ctx = context.copy()
            ctx['fiscalyear_id'] = self.pool.get('account.period').browse(cr, uid, invoice.period_id.id).fiscalyear_id.id
            number = self.pool.get('ir.sequence').get_id(cr, uid, sequence.id, context=ctx)
            
            self.write(cr, uid, [invoice.id], {
                'number': number,
            }, context)
        return super(account_invoice, self).action_number(cr, uid, ids, context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

