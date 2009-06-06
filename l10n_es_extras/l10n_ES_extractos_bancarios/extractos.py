# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                    Jordi Esteve <jesteve@zikzakmedia.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv,fields
import tools
import os

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
        }
l10n_es_extractos_concepto()


class account_bank_statement_line(osv.osv):
    _inherit = "account.bank.statement.line"

    def onchange_partner_id(self, cursor, user, line_id, partner_id, type, currency_id, context={}):
        """Elimina el precálculo del importe de la línea del extracto bancario"""
        res = super(account_bank_statement_line, self).onchange_partner_id(cursor, user, line_id, partner_id, type, currency_id, context=context)
        # devuelve res = {'value': {'amount': balance, 'account_id': account_id}}
        del res['value']['amount']
        return res
account_bank_statement_line()
