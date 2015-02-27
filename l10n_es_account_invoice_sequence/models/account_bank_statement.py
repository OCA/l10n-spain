# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L.
#                    http://www.NaN-tic.com
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2014 Domatix (http://www.domatix.com)
#                       Angel Moya <angel.moya@domatix.com>
#    Copyright (c) 2014 Eduardo Calleja <e.calleja.garcia@gmail.com>
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

from openerp.osv import osv
import logging
_logger = logging.getLogger("Starlab:Custom")

class account_bank_statement(osv.osv):
    _inherit = 'account.bank.statement'

    def _prepare_move(self, cr, uid, st_line, st_line_number, context=None):
        """Prepare the dict of values to create the move from a
           statement line. This method overrides the generic method on 
           account bank statement module in order to adapt it to l10n_es.

           :param browse_record st_line: account.bank.statement.line record to
                  create the move from.
           :param char st_line_number: will be used as the name of the generated account move
           :return: dict of value to create() the account.move
        """
        re = super(account_bank_statement, self)._prepare_move(cr, uid, st_line, st_line_number, context)

        #Retrieving spanish journal sequence
        re['name'] = st_line.journal_id.sequence_id.id

        return re

