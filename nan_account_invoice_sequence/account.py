# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L. All Rights Reserved.
#                    http://www.NaN-tic.com
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

from osv import osv
from osv import fields
from tools.translate import _

class account_journal(osv.osv):
    _inherit = 'account.journal'

    _columns = {
        'invoice_sequence_id': fields.many2one('ir.sequence', 'Invoice Sequence', domain="[('company_id','=',company_id)]", help="The sequence used for invoice numbers in this journal."),
    }

    def _check_company(self, cr, uid, ids):
        for journal in self.browse(cr, uid, ids):
            if journal.invoice_sequence_id and journal.invoice_sequence_id.company_id != journal.company_id:
                raise osv.except_osv(_('Invoice Sequence Error'), _("The company of invoice sequence does not match journal's company."))
        return True

    _constraints = [ (_check_company, 'Journal company and invoice sequence company do not match.', ['company_id','invoice_sequence_id']) ]
account_journal()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

