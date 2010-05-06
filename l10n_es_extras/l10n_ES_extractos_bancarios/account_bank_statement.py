# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2010 Pexego Sistemas Informáticos. All Rights Reserved
#                       Borja López Soilán <borjals@pexego.es>
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

"""
C43 format concepts and extension of the bank statement lines.
"""

from osv import osv

class account_bank_statement_line(osv.osv):
    """
    Extends the bank statement lines to try to set the right reconciliation
    for lines edited by hand.
    """

    _inherit = "account.bank.statement.line"

    def onchange_partner_id(self, cr, uid, line_id, partner_id, ptype, currency_id, amount, reconcile_id, context={}):
        """Elimina el precálculo del importe de la línea del extracto bancario
            y propone una conciliación automática si encuentra una."""
        statement_reconcile_obj = self.pool.get('account.bank.statement.reconcile')
        move_line_obj = self.pool.get('account.move.line')
        res = super(account_bank_statement_line, self).onchange_partner_id(cr, uid, line_id, partner_id, ptype, currency_id, context=context)

        # devuelve res = {'value': {'amount': balance, 'account_id': account_id}}
        if 'value' in res and 'amount' in res['value']:
            del res['value']['amount']

        # Eliminamos la propuesta de concilacion que hubiera
        if reconcile_id:
            statement_reconcile_obj.unlink(cr, uid, [reconcile_id])
            if 'value' not in res:
                res['value'] = {}
            res['value']['reconcile_id'] = False

        # Busqueda del apunte por importe con partner
        if partner_id and amount:
            domain = [
                ('reconcile_id', '=', False),
                ('account_id.type', 'in', ['receivable', 'payable']),
                ('partner_id', '=', partner_id),
            ]
            if amount >= 0:
                domain.append( ('debit', '=', '%.2f' % amount) )
            else:
                domain.append( ('credit', '=', '%.2f' % -amount) )
            line_ids = move_line_obj.search(cr, uid, domain, context=context)
            # Solamente crearemos la conciliacion automatica cuando exista un solo apunte
            # que coincida. Si hay mas de uno el usuario tendra que conciliar manualmente y
            # seleccionar cual de ellos es el correcto.
            if len(line_ids) == 1:
                res['value']['reconcile_id'] = statement_reconcile_obj.create(cr, uid, {
                    'line_ids': [(6, 0, line_ids)],
                }, context=context)
        return res
account_bank_statement_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
