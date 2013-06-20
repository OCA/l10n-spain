# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2012 Acysos S.L. (http://acysos.com) All Rights Reserved.
#                       Ignacio Ibeas <ignacio@acysos.com>
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

from tools.translate import _
from osv import osv, fields

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    _columns = {
        'is_ticket_summary': fields.boolean('Ticket Summary', help='Check if this invoice is a ticket summary'),
        'number_tickets': fields.integer('Number of tickets', digits=(12,0)),
        'first_ticket': fields.char('First ticket', size=40),
        'last_ticket': fields.char('Last ticket', size=40)
    }
    
account_invoice()