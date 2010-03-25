# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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

from osv import osv,fields
import tools
import os
from tools.translate import _

class l10n_es_extractos_import_wizard(osv.osv_memory):
    _name = 'l10n.es.extractos.import.wizard'

    def action_import(self, cr, uid, ids, context=None):
        try:
            fp = tools.file_open(os.path.join('l10n_ES_extractos_bancarios', 'extractos_conceptos.xml'))
        except IOError, e:
            return {}
        idref = {}
        tools.convert_xml_import(cr, 'l10n_ES_extractos_bancarios', fp,  idref, 'init', noupdate=True)
        return {}
l10n_es_extractos_import_wizard()


class l10n_es_extractos_concepto(osv.osv):
    _name = 'l10n.es.extractos.concepto'
    _description = 'C43 codes'

    _columns = {
        'code': fields.char('Concept code', size=2, select=True, required=True, help='2 digits code of the concept defined in the file of C43 bank statements'),
        'name': fields.char('Concept name', size=64, select=True, required=True),
        'account_id': fields.many2one('account.account', 'Account associated to the concept', domain=[('type','<>','view'), ('type', '<>', 'closed')], select=True, required=True, help='Default account to be associated with the concept when the file of C43 bank statements is imported'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    def _default_company(self, cr, uid, context={}):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id:
            return user.company_id.id
        return self.pool.get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]

    _defaults = {
        'company_id': _default_company,
    }

l10n_es_extractos_concepto()


class account_bank_statement_line(osv.osv):
    _inherit = "account.bank.statement.line"

    def onchange_partner_id(self, cursor, user, line_id, partner_id, type, currency_id, amount, reconcile_id, context={}):
        """Elimina el precálculo del importe de la línea del extracto bancario
            y propone una conciliación automática si encuentra una."""
        statement_reconcile_obj = self.pool.get('account.bank.statement.reconcile')
        move_line_obj = self.pool.get('account.move.line')
        res = super(account_bank_statement_line, self).onchange_partner_id(cursor, user, line_id, partner_id, type, currency_id, context=context)

        # devuelve res = {'value': {'amount': balance, 'account_id': account_id}}
        if 'value' in res and 'amount' in res['value']:
            del res['value']['amount']

        # Eliminamos la propuesta de concilacion que hubiera
        if reconcile_id:
            statement_reconcile_obj.unlink(cursor, user, [reconcile_id])
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
            line_ids = move_line_obj.search(cursor, user, domain, context=context)
            # Solamente crearemos la conciliacion automatica cuando exista un solo apunte
            # que coincida. Si hay mas de uno el usuario tendra que conciliar manualmente y
            # seleccionar cual de ellos es el correcto.
            if len(line_ids) == 1:
                res['value']['reconcile_id'] = statement_reconcile_obj.create(cursor, user, {
                    'line_ids': [(6, 0, line_ids)],
                }, context=context)
        return res
account_bank_statement_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
