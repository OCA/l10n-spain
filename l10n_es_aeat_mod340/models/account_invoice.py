# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2012 Acysos S.L. (http://acysos.com)
#                       Ignacio Ibeas <ignacio@acysos.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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
import logging

from openerp import api
from openerp.osv import fields, orm

_logger = logging.getLogger(__name__)


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'

    _columns = {
        'is_ticket_summary': fields.boolean(
            'Ticket Summary',
            help='Check if this invoice is a ticket summary'),
        'number_tickets': fields.integer('Number of tickets', digits=(12, 0)),
        'first_ticket': fields.char('First ticket', size=40),
        'last_ticket': fields.char('Last ticket', size=40)
    }

    @api.one
    def is_leasing_invoice(self):
        lines = self.env['account.invoice.line'].search(
            [('invoice_id', '=', self.id),
                ('account_id.is_340_leasing_account', '=', True)])
        if lines:
            return True
        return False

    @api.one
    def is_reverse_charge_invoice(self):
        lines = self.env['account.invoice.line'].search(
            [('invoice_id', '=', self.id),
                ('invoice_line_tax_id.is_340_reserve_charge', '=', True)])
        if lines:
            return True
        return False


    @api.multi
    def check_reference_required(self):
        if self.type == 'in_invoice':
            if self.reference is False:
                return False
            else:
                return True
        else:
            return True
