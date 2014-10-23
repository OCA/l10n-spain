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
        sequence_obj = self.pool['ir.sequence']
        period_obj = self.pool['account.period']
        for inv in self:
            if inv.internal_number:
                number = inv.internal_number
            else:
                sequence = inv.journal_id.invoice_sequence_id
                if not sequence:
                    raise exceptions.Warning(
                        _('Error!:: Journal %s has no sequence defined for'
                          'invoices.') % inv.journal_id.name)

                ctx = self.env.context.copy()
                period = period_obj.browse(self.env.cr, self.env.uid,
                                           inv.period_id.id)
                ctx['fiscalyear_id'] = period.fiscalyear_id.id
                number = sequence_obj.next_by_id(self.env.cr, self.env.uid,
                                                 sequence.id, ctx)

            inv.number = number
        return super(AccountInvoice, self).action_number()
