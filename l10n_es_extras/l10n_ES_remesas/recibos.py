# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2006 ACYSOS S.L.. (http://acysos.com) All Rights Reserved.
#    Pedro Tarrafeta <pedro@acysos.com>
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

from osv import osv, fields, orm
import netsvc
logger = netsvc.Logger()

class account_move_line(osv.osv):
    _name = 'account.move.line'
    _inherit = 'account.move.line'

    def _invoice_n(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        for rec in self.browse(cr, uid, ids, context):
            cr.execute("SELECT id, number FROM account_invoice WHERE move_id = %d", (rec.move_id.id,))
            res = cr.fetchall()
#            logger.notifyChannel('Facturas...', netsvc.LOG_INFO, res)
            if res:
                result[rec.id] = res[0]
            else:
                result[rec.id] = (0,0)
        return result

    _columns = {
        'cheque_recibido': fields.boolean('Cheque Recibido'),
        'invoice_id':fields.function(_invoice_n, method=True, type="many2one", relation="account.invoice", string="Factura"),
        'acc_number': fields.many2one('res.partner.bank','Account number', select=True,),
    }
account_move_line()
