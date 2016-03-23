# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L.
#                    http://www.NaN-tic.com
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2014 Domatix (http://www.domatix.com)
#                       Angel Moya <angel.moya@domatix.com>
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
from openerp import models, fields, api, _, exceptions


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    number = fields.Char(related=False, size=32, copy=False)
    invoice_number = fields.Char(copy=False)

    @api.multi
    def action_number(self):
        for inv in self:
            if not inv.invoice_number:
                sequence = inv.journal_id.invoice_sequence_id
                if sequence:
                    number = sequence.with_context({
                        'fiscalyear_id': inv.period_id.fiscalyear_id.id
                    }).next_by_id(sequence.id)
                else:
                    # TODO: raise an error if the company is flagged
                    #       as requiring a separate numbering for invoices
                    number = inv.move_id.name
                inv.write({
                    'number': number,
                    'invoice_number': number
                })
            else:
                inv.write({
                    'number': inv.invoice_number,
                })
            if inv.move_id.ref:
                inv.move_id.ref += " - %s" % inv.invoice_number
            else:
                inv.move_id.ref = inv.invoice_number
        re = super(AccountInvoice, self).action_number()
        for inv in self:
            inv.write({'internal_number': inv.move_id.name})
        return re

    @api.multi
    def unlink(self):
        self.write({'internal_number': False})
        return super(AccountInvoice, self).unlink()
