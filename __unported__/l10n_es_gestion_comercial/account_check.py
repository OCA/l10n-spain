# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2011 Soluntec - Soluciones Tecnológicas (http://www.soluntec.es) All Rights Reserved.
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################


from osv import osv
from osv import fields
import time


class account_issued_check(osv.osv):

    '''
    Account Issued Check
    '''
    _name = 'account.issued.check'
    _description = 'Manage Checks'

    _columns = {
        'number': fields.char('Numero de Documento', size=20, required=True),
        'amount': fields.float('Cantidad del Documento', required=True),
        'date_out': fields.date('Fecha de ingreso', required=True),
        'date': fields.date('Fecha', required=True),
        'debit_date': fields.date('Fecha de Emision', readonly=True),
        'date_changed': fields.date('Fecha de Cambio', readonly=True),
        'receiving_partner_id': fields.many2one('res.partner', 'Entidad Receptora', required=False, readonly=True),
        'bank_id': fields.many2one('res.bank', 'Banco', required=True),
        'on_order': fields.char('A la Orden', size=64),
        'signatory': fields.char('Firmante', size=64),
        'clearing': fields.selection((
            ('24', '24 hs'),
            ('48', '48 hs'),
            ('72', '72 hs'),
        ), 'Tiempo Efecto'),
        'origin': fields.char('Origen', size=64),
        'account_bank_id': fields.many2one('res.partner.bank', 'Cuenta Destino'),
        'voucher_id': fields.many2one('account.voucher', 'Comprobante', required=True),
        'issued': fields.boolean('Emitido'),
        'picture':    	fields.binary('Image'),

    }
    _rec_name = 'number'

    _defaults = {
        'clearing': lambda *a: '24',
    }

account_issued_check()


class account_third_check(osv.osv):

    '''
    Account Third Check
    '''
    _name = 'account.third.check'
    _description = 'Manage Checks'

    _columns = {
        'number': fields.char('Numero de Documento', size=20, required=True),
        'amount': fields.float('Cantidad de Documento', required=True),
        'date_in': fields.date('Fecha de Ingreso', required=True),
        'date': fields.date('Fecha de Documento', required=True),
        'date_out': fields.date('Fecha de Emision', readonly=True),
        'source_partner_id': fields.many2one('res.partner', 'Empresa Origen', required=False, readonly=True),
        'destiny_partner_id': fields.many2one('res.partner', 'Empresa Destino', readonly=False, required=False, states={'delivered': [('required', True)]}),
        'state': fields.selection((
            ('draft', 'Draft'),
            ('C', 'En Cartera'),
            ('deposited', 'Deposited'),
            ('delivered', 'Delivered'),
            ('rejected', 'Rejected'),
        ), 'State', required=True),
        'bank_id': fields.many2one('res.bank', 'Banco', required=True),
        'on_order': fields.char('A la Orden', size=64),
        'signatory': fields.char('Firmante', size=64),
        'clearing': fields.selection((
            ('24', '24 hs'),
            ('48', '48 hs'),
            ('72', '72 hs'),
        ), 'Tiempo Efecto'),
        'origin': fields.char('Origen', size=64),
        'account_bank_id': fields.many2one('res.partner.bank', 'Cuenta Destino'),
        'voucher_id': fields.many2one('account.voucher', 'Comprobante', required=True),
        'reject_debit_note': fields.many2one('account.invoice', 'Debito Por Rechazo'),
        'picture':    	fields.binary('Image'),
    }

    _rec_name = 'number'
    _defaults = {
        'date_in': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'clearing': lambda *a: '24',
    }

account_third_check()
