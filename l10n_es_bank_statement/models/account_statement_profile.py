# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) All rights reserved:
#        2013-2014 Servicios Tecnológicos Avanzados (http://serviciosbaeza.com)
#                  Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
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
from openerp.osv import orm


account_concept_mapping = {
    '01': '4300%00',
    '02': '4100%00',
    '03': '4100%00',
    '04': '4300%00',
    '05': '6800%00',
    '06': '4010%00',
    '07': '5700%00',
    '08': '6800%00',
    '09': '2510%00',
    '10': '5700%00',
    '11': '5700%00',
    '12': '5700%00',
    '13': '5730%00',
    '14': '4300%00',
    '15': '6400%00',
    '16': '6690%00',
    '17': '6690%00',
    '98': '5720%00',
    '99': '5720%00',
}


class AccountStatementProfile(orm.Model):
    _inherit = "account.statement.profile"

    def prepare_statement_lines_vals(self, cr, uid, parser_vals, statement_id,
                                     context):
        """Complete values filling default account for each type of C43
        operation.
        """
        vals = super(AccountStatementProfile, self
                     ).prepare_statement_lines_vals(cr, uid, parser_vals,
                                                    statement_id, context)
        if vals.get('c43_concept'):
            account_obj = self.pool['account.account']
            account_ids = account_obj.search(
                cr, uid, [('code', 'like',
                           account_concept_mapping[vals['c43_concept']])],
                context=context)
            if account_ids:
                vals['account_id'] = account_ids[0]
        return vals
