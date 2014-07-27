# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L.
#                    http://www.NaN-tic.com
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
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
from openerp.osv import orm, fields


class AccountJournal(orm.Model):
    _inherit = 'account.journal'

    _columns = {
        'invoice_sequence_id': fields.many2one(
            'ir.sequence',
            'Invoice sequence',
            domain="[('company_id','=',company_id)]",
            help="The sequence used for invoice numbers in this journal.",
            ondelete='restrict'),
    }

    def _check_company(self, cr, uid, ids):
        for journal in self.browse(cr, uid, ids):
            if (journal.invoice_sequence_id and
                    journal.invoice_sequence_id.company_id !=
                    journal.company_id):
                return False
        return True

    _constraints = [
        (_check_company,
         'Journal company and invoice sequence company do not match.',
         ['company_id', 'invoice_sequence_id'])
    ]
