# -*- coding: utf-8 -*-
# Copyright 2012 - Acysos S.L. (http://acysos.com)
#                - Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2016 - Tecnativa - Angel Moya <odoo@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    is_ticket_summary = fields.Boolean(string='Ticket Summary', help='Check if this invoice is a ticket summary')
    number_tickets = fields.Integer(string='Number of tickets')
    first_ticket = fields.Char(string='First ticket', size=40)
    last_ticket = fields.Char(string='Last ticket', size=40)
