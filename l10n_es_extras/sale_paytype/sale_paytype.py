# -*- encoding: utf-8 -*-

##############################################################################
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

import netsvc
from osv import fields, osv


# añadimos a pedidos de venta los campos relativos a la forma de pago 
class sale_order(osv.osv):
    _inherit='sale.order'
    _columns={
        'tipopago_id': fields.many2one('account.paytype', 'Tipo de Pago'),    
        'acc_number': fields.many2one('res.partner.bank','Account number', select=True,),    
        'payment_term': fields.many2one('account.payment.term', 'Payment Term',readonly=True, states={'draft':[('readonly',False)]} ),        
    }
    
    def onchange_partner_id2(self, cr, uid, ids, part):
        # Copia los datos del partner en el pedido, incluyendo payment_term y el nuevo campo tipopago_id
        result = self.onchange_partner_id(cr, uid, ids, part)
        tipopago_id = False
        if part:
            partner_line = self.pool.get('res.partner').browse(cr, uid, part)
            if partner_line:
                tipopago_id = partner_line.tipopago_id.id
                result['value']['tipopago_id'] = tipopago_id
                result['value']['payment_term'] = partner_line.property_payment_term.id
                
        return self.onchange_tipopago_id(cr, uid, ids, tipopago_id, part, result)

    def onchange_tipopago_id(self, cr, uid, ids, tipopago_id, partner_id, result = {'value': {}}):
        if tipopago_id and partner_id: 
            if self.pool.get('account.paytype').browse(cr, uid, [tipopago_id])[0].link_bank: # Si la forma de pago está asociada a una cuenta bancaria
                partner_bank_obj = self.pool.get('res.partner.bank')
                args = [('partner_id', '=', partner_id), ('default_bank', '=', 1)]
                bank_account_id = partner_bank_obj.search(cr, uid, args)
                if bank_account_id:
                    result['value']['acc_number'] = bank_account_id[0]
                    return result
        result['value']['acc_number'] = False
        return result

    # redefinimos _make_invoice para que 
    # la factura generada recoja el payment_term, tipopago_id y acc_number del pedido de venta.
    def _make_invoice(self, cr, uid, order, lines):
        inv_id = super(sale_order, self)._make_invoice(cr, uid, order, lines)
        inv_obj = self.pool.get('account.invoice').browse(cr, uid, [inv_id])[0]
        inv_obj.write(cr, uid, inv_id, {'payment_term':order.payment_term.id,'tipopago_id':order.tipopago_id.id,'acc_number':order.acc_number.id}, None)
        return inv_id    
    
sale_order()
