# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2006 ACYSOS S.L.. (http://acysos.com) All Rights Reserved.
#    Pedro Tarrafeta <pedro@acysos.com>
#
# Corregido para instalación TinyERP estándar 4.2.0: Zikzakmedia S.L. 2008
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Añadidas cuentas de remesas y tipos de pago. 2008
#    Pablo Rocandio <salbet@gmail.com>
#
# Corregido para instalación OpenERP 5.0.0 sobre account_payment_extension: Zikzakmedia S.L. 2009
#   Jordi Esteve <jesteve@zikzakmedia.com>
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
logger = netsvc.Logger()
from osv import osv, fields, orm
import ir
import time
import base64

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

import pooler


class payment_mode(osv.osv):
    _name= 'payment.mode'
    _inherit = 'payment.mode'


    def _get_cif(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for line in self.browse(cr, uid, ids):
            if line.partner_id:
                res[line.id] = line.partner_id.vat
            else:
                res[line.id] = ""
        return res

    def onchange_partner(self, cr, uid, ids, partner_id):
        if partner_id:
            pool = pooler.get_pool(cr.dbname)
            obj = pool.get('res.partner')
            field = ['name']
            ids = [partner_id]
            filas = obj.read(cr, uid, ids, field) 
            return {'value':{'nombre': filas[0]["name"][:40]}}
        return {'value':{'nombre': ""}}

    _columns = {
        'tipo': fields.selection([('none','None'),('csb_19','CSB 19'),('csb_58','CSB 58')], 'Tipo de remesa', size=6, select=True, required=True),
        'sufijo': fields.char('Sufijo',size=3, select=True),
        #'remesas': fields.one2many('remesas.remesa', 'banco', 'Remesas'),
        'partner_id': fields.many2one('res.partner', 'Partner', select=True),
        'nombre': fields.char('Nombre Empresa para fichero', size=40),
        'cif': fields.function(_get_cif, method=True, string='CIF', type="char", select=True),
        }

    _defaults = {
        'tipo': lambda *a: 'none',
        'sufijo': lambda *a: '000',
    }
    #_columns= {
        #'name': fields.char('Name', size=64, required=True,help='Mode of Payment'),
        #'bank_id': fields.many2one('res.partner.bank', "Bank account",
            #required=True,help='Bank Account for the Payment Mode'),
        #'journal': fields.many2one('account.journal', 'Journal', required=True,
            #domain=[('type', '=', 'cash')],help='Cash Journal for the Payment Mode'),
        #'type': fields.many2one('payment.type','Payment type',required=True,help='Select the Payment Type for the Payment Mode.'),
    #}

payment_mode()


class payment_order(osv.osv):
    _name = 'payment.order'
    _inherit = 'payment.order'

    def get_wizard(self, type):
        if type == 'RECIBO_CSB':
            return (self._module, 'wizard_account_payment_remesas_create')
        else:
            return super(payment_order, self).get_wizard(type)

payment_order()


    #_columns={ 
        #'name': fields.char('Codigo de remesa', size=15),
        #'cuenta_id': fields.many2one('remesas.cuenta','Cuenta de remesas', required=True, ),
        #'total': fields.function(_total, method=True, string='Importe Total' ),
        #'fecha': fields.date('Fecha'),
        #'fecha_cargo': fields.date('Fecha Cargo (C19)'),
        #'diario': fields.many2one('account.journal', 'Diario asiento cobro'),
        #'account_id': fields.many2one('account.account', 'Cuenta asiento bancario', domain=[('type','<>','view'), ('type', '<>', 'closed')]),
        #'receipts': fields.one2many('account.move.line', 'remesa_id' ,'Recibos', readonly=True, states={'draft':[('readonly',False)]}),
        #'texto': fields.text('Texto para el banco'),
        #'state': fields.selection( (('draft','Borrador'),('confirmed','Confirmada'),('2reconcile','A Conciliar'),('done','Realizada')), 'Estado', readonly=True),
        #'agrupar_recibos': fields.boolean('Agrupar Recibos'),
        #'asiento': fields.many2one('account.move', 'Asiento de Cobro', readonly=True),
        #'fichero': fields.binary('Fichero para el banco', readonly=True),
    #}
