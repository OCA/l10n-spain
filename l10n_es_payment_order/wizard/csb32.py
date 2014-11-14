# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2006 ACYSOS S.L. (http://acysos.com)
#                       Pedro Tarrafeta <pedro@acysos.com>
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com)
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
#
# Corregido para instalación TinyERP estándar 4.2.0: Zikzakmedia S.L. 2008
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Añadidas cuentas de remesas y tipos de pago. 2008
#    Pablo Rocandio <salbet@gmail.com>
#
# Rehecho de nuevo para instalación OpenERP 5.0.0 sobre
# account_payment_extension: Zikzakmedia S.L. 2009
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Refactorización. Acysos S.L. (http://www.acysos.com) 2012
#   Ignacio Ibeas <ignacio@acysos.com>
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
from datetime import datetime
from openerp.tools.translate import _
from .log import Log


class Csb32(orm.Model):
    _name = 'csb.32'
    _auto = False

    def _cabecera_fichero_32(self, cr, uid):
        converter = self.pool['payment.converter.spain']
        texto = '0265'
        texto += '  '
        texto += datetime.today().strftime('%d%m%y')
        texto += converter.digits_only(cr, uid, self.order.reference)[-4:]
        texto += ' ' * 35
        texto += converter.digits_only(
            cr, uid, self.order.mode.bank_id.acc_number)[:8]
        texto += ' ' * 6
        texto += ' ' * 61
        texto += ' ' * 24
        texto += '\r\n'
        if len(texto) != 152:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 150 '
                        'characters long:\n%s') %
                      ('Cabecera fichero 32', texto), True)
        return texto

    def _cabecera_remesa_32(self, cr, uid, context):
        converter = self.pool['payment.converter.spain']
        # A:
        texto = '1165'
        texto += '  '
        # B
        texto += datetime.today().strftime('%d%m%y')
        texto += '0001'
        texto += ' ' * 12
        # C
        # TODO: Identificador del cedente. Qué es?
        texto += converter.convert(
            cr, uid, self.order.mode.cedente, 15, context)
        texto += '1'  # Identificativo de efectos truncados
        texto += ' ' * 21
        # D
        texto += converter.digits_only(cr, uid,
                                       self.order.mode.bank_id.acc_number)
        texto += converter.digits_only(cr, uid,
                                       self.order.mode.bank_id.acc_number)
        texto += converter.digits_only(cr, uid,
                                       self.order.mode.bank_id.acc_number)
        texto += ' ' + ' ' * 24
        texto += '\r\n'
        if len(texto) != 152:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 150 '
                        'characters long:\n%s') %
                      ('Cabecera remesa 32', texto), True)
        return texto

    def _registro_individual_i_32(self, cr, uid, recibo, context):
        converter = self.pool['payment.converter.spain']
        # A
        texto = '2565'
        texto += '  '
        # B
        texto += converter.convert(cr, uid, self.num_recibos + 1, 15, context)
        texto += datetime.today().strftime('%d%m%y')
        texto += '0001'
        # C
        state = (self.order.mode.bank_id.state_id and
                 self.order.mode.bank_id.state_id.code or False)
        texto += converter.convert(cr, uid, state, 2, context)
        texto += ' ' * 7
        texto += '  '
        # D
        texto += converter.convert(
            cr, uid, self.order.mode.bank_id.city, 20, context)
        texto += ' '
        # E
        texto += ' ' * 24
        texto += converter.convert(cr, uid, abs(recibo['amount']), 9, context)
        texto += ' ' * 15
        texto += datetime.strptime(
            recibo['ml_maturity_date'], '%Y-%m-%d').strftime('%d%m%y')
        texto += ' ' * (6 + 6 + 1 + 4 + 16)
        texto += '\r\n'
        if len(texto) != 152:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 150 '
                        'characters long:\n%s') %
                      ('Registro individual I 32', texto), True)
        return texto

    def _registro_individual_ii_32(self, cr, uid, recibo, context):
        converter = self.pool['payment.converter.spain']
        # A: Identificacion de la operacion
        texto = '2665'
        texto += '  '
        # B: Datos del efecto
        texto += converter.convert(cr, uid, self.num_recibos + 1, 15, context)
        texto += '  '
        texto += '2'  # Recibo
        texto += '000000'
        texto += '1'
        # 0= Sin gastos, 1=Con gastos, 9=Orden expresa de protesto notarial
        texto += '0'
        # C: Datos del efecto
        ccc = recibo['bank_id'] and recibo['bank_id'].acc_number or ''
        if ccc:
            texto += ccc[:20].zfill(20)
        else:
            texto += ' ' * 20
        # D: Datos del efecto
        texto += converter.convert(cr, uid, self.order.mode.partner_id.name,
                                   34, context)
        texto += converter.convert(
            cr, uid, recibo['partner_id'].name, 34, context)
        texto += ' ' * 30
        texto += '\r\n'
        if len(texto) != 152:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 150 '
                        'characters long:\n%s') %
                      ('Registro individual II 32', texto), True)
        return texto

    def _registro_individual_iii_32(self, cr, uid, recibo, context):
        converter = self.pool['payment.converter.spain']
        # A: Identificacion de la operacion
        texto = '2765'
        texto += '  '

        # B: Datos del efecto
        texto += converter.convert(cr, uid, self.num_recibos + 1, 15, context)
        texto += '  '
        addresses = self.pool['res.partner'].address_get(
            cr, uid, [recibo['partner_id'].id])
        # if not addresses:
        #    print "NO ADDRESSES"
        address = self.pool['res.partner'].browse(cr, uid,
                                                  addresses['default'],
                                                  context)
        texto += converter.convert(cr, uid, address.street, 34, context)
        texto += converter.convert(cr, uid, address.zip, 5, context)
        texto += converter.convert(cr, uid, address.city, 20, context)
        texto += converter.convert(cr, uid, address.state_id and
                                   address.state_id.code or False, 2, context)
        texto += '0' * 7
        # C: Datos del efecto
        vat = (recibo['partner_id'].vat and recibo['partner_id'].vat[2:] or
               False)
        texto += converter.convert(cr, uid, vat, 9, context)
        texto += ' ' * 50
        texto += '\r\n'
        if len(texto) != 152:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 150 '
                        'characters long:\n%s') %
                      ('Registro individual III 32', texto), True)
        return texto

    def _registro_fin_remesa_32(self, cr, uid, context):
        converter = self.pool['payment.converter.spain']
        # A: Identificación de la operación
        texto = '7165'
        texto += '  '
        # B: Control de duplicidades
        texto += datetime.today().strftime('%d%m%y')
        texto += '0001'
        texto += ' ' * (6 + 6)
        # C: Libre
        texto += ' ' * 37
        # D: Acumuladores de importe
        texto += ' ' * 10
        texto += converter.convert(cr, uid, abs(self.order.total), 10, context)
        texto += ' ' * (10 + 6 + 7 + 6 + 6 + 6)
        # E: Controles de lectura de fichero
        texto += ' ' * 5
        texto += converter.convert(cr, uid, (self.num_recibos * 3) + 2, 7,
                                   context)
        texto += converter.convert(cr, uid, self.num_recibos, 6, context)
        texto += ' ' * 6
        texto += '\r\n'
        if len(texto) != 152:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 150 '
                        'characters long:\n%s') %
                      ('Fin remesa 32', texto), True)
        return texto

    def _registro_fin_fichero_32(self, cr, uid, context):
        converter = self.pool['payment.converter.spain']
        # A: Identificación de la operación
        texto = '9865'
        texto += '  '
        # B: Libre
        texto += ' ' * 22
        # C: Libre
        texto += ' ' * 37
        # D: Acumuladores de importes
        texto += ' ' * 10
        texto += converter.convert(cr, uid, abs(self.order.total), 10, context)
        texto += ' ' * (10 + 6 + 7 + 6 + 6 + 6)
        # E: Controles de lectura del fichero
        texto += '00001'
        texto += converter.convert(cr, uid, (self.num_recibos * 3) + 3, 7,
                                   context)
        texto += converter.convert(cr, uid, self.num_recibos, 6, context)
        texto += ' ' * 6
        texto += '\r\n'
        if len(texto) != 152:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 150 '
                        'characters long:\n%s') % ('Fin fichero 32', texto),
                      True)
        return texto

    def create_file(self, cr, uid, order, lines, context):
        self.order = order
        txt_remesa = ''
        self.num_recibos = 0
        self.num_lineas_opc = 0
        txt_remesa += self._cabecera_fichero_32(cr, uid)
        txt_remesa += self._cabecera_remesa_32(cr, uid, context)
        for recibo in lines:
            txt_remesa += self._registro_individual_i_32(cr, uid, recibo,
                                                         context)
            txt_remesa += self._registro_individual_ii_32(cr, uid, recibo,
                                                          context)
            txt_remesa += self._registro_individual_iii_32(cr, uid, recibo,
                                                           context)
            self.num_recibos = self.num_recibos + 1
        txt_remesa += self._registro_fin_remesa_32(cr, uid, context)
        txt_remesa += self._registro_fin_fichero_32(cr, uid, context)
        return txt_remesa
