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

class l10n_es_extractos_concepto(osv.osv):
	_name = 'l10n.es.extractos.concepto'
	_description = 'Códigos C43'
		
	_columns = {
		'code': fields.char('Código concepto', size=2, select=True, required=True, help='Código de 2 dígitos del concepto definido en el fichero de extractos bancarios C43'),
		'name': fields.char('Nombre concepto', size=64, select=True, required=True),
		'account_id': fields.many2one('account.account', 'Cuenta asociada al concepto', domain=[('type','<>','view'), ('type', '<>', 'closed')], select=True, required=True, help='Cuenta contable por defecto que se asociará al concepto al importar el fichero de extractos bancarios C43'),
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