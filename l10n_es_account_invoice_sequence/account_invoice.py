# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L. All Rights Reserved.
#                    http://www.NaN-tic.com
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2014 Domatix (http://www.domatix.com)
#                       Angel Moya <angel.moya@domatix.com>
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
from openerp import models, fields, api, _
from openerp.exceptions import except_orm

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({'invoice_number' : False})
        default.update({'number' : False})
        return super(account_invoice, self).copy(cr, uid, id, default,
                                                 context=context)

    number = fields.Char('Invoice Number', size=32, readonly=True,
                help="Unique number of the invoice, computed automatically "
                     "when the invoice is created.")
    
    @api.multi
    def action_number(self):
        
        
        for inv in self:

            sequence = inv.journal_id.invoice_sequence_id
            if not sequence:
                raise except_orm(_('Error!'),
                    _('Journal %s has no sequence defined for invoices.')
                    %inv.journal_id.name)
            ctx = self.env.context.copy()
            period_obj = self.pool.get('account.period')
            ctx['fiscalyear_id'] = period_obj.browse(self.env.cr, self.env.uid,
                                        inv.period_id.id).fiscalyear_id.id
            sequence_obj = self.pool.get('ir.sequence')
            number = sequence_obj.next_by_id(self.env.cr, self.env.uid, sequence.id, ctx)
            inv.write({'number': number})
            
        result = super(account_invoice, self).action_number()
            
        return result
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
