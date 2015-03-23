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

from openerp import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    is_ticket_summary = fields.Boolean(string='Ticket Summary',
                                       help='Check if this invoice is a '
                                       'ticket summary')
    number_tickets = fields.Integer(string='Number of tickets', digits=(12, 0))
    first_ticket = fields.Char(string='First ticket', size=40)
    last_ticket = fields.Char(string='Last ticket', size=40)
