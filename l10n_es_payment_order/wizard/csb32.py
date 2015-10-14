# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2006 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#                       Pedro Tarrafeta <pedro@acysos.com>
#                       Ignacio Ibeas <ignacio@acysos.com>
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights
#                       Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#
#    Migración Odoo 8.0. Acysos S.L. (http://www.acysos.com) 2015
#    Ignacio Ibeas <ignacio@acysos.com>
#    $Id$
#
# Corregido para instalación TinyERP estándar 4.2.0: Zikzakmedia S.L. 2008
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Añadidas cuentas de remesas y tipos de pago. 2008
#    Pablo Rocandio <salbet@gmail.com>
#
# Rehecho de nuevo para instalación OpenERP 5.0.0 sobre
#   account_payment_extension: Zikzakmedia S.L. 2009
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

from openerp import models, api, _
from datetime import datetime
from log import *


class Csb32(models.Model):
    _name = 'csb.32'
    _auto = False

    @api.model
    def _cabecera_fichero_32(self):
        converter = self.env['payment.converter.spain']
        texto = '0265'
        texto += '  '
        texto += datetime.today().strftime('%d%m%y')
        texto += converter.digits_only(self.order.reference)[-4:]
        texto += ' '*35
        texto += converter.digits_only(self.order.mode.bank_id.acc_number)[:8]
        texto += ' '*6
        texto += ' '*61
        texto += ' '*24
        texto += '\r\n'
        if len(texto) != 152:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 150 '
                        'characters long:\n%s') % ('Cabecera fichero 32',
                                                   texto), True)
        return texto

    @api.model
    def _cabecera_remesa_32(self):
        converter = self.env['payment.converter.spain']
        # A:
        texto = '1165'
        texto += '  '

        # B
        texto += datetime.today().strftime('%d%m%y')
        texto += '0001'
        texto += ' '*12

        # C
        texto += converter.convert(self.order.mode.csb32_assignor, 15)
        # Identificativo de efectos truncados
        texto += '1'
        texto += ' '*21

        # D
        texto += converter.digits_only(self.order.mode.bank_id.acc_number)
        texto += converter.digits_only(self.order.mode.bank_id.acc_number)
        texto += converter.digits_only(self.order.mode.bank_id.acc_number)
        texto += ' ' + ' ' * 24
        texto += '\r\n'
        if len(texto) != 152:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 150 '
                        'characters long:\n%s') % ('Cabecera remesa 32',
                                                   texto), True)
        return texto

    @api.model
    def _registro_individual_i_32(self, recibo):
        converter = self.env['payment.converter.spain']
        # A
        texto = '2565'
        texto += '  '
        # B
        texto += converter.convert(self.num_recibos+1, 15)
        texto += datetime.today().strftime('%d%m%y')
        texto += '0001'

        # C
        bank_state_id = self.order.mode.bank_id.state_id
        state = bank_state_id and bank_state_id.code or False
        texto += converter.convert(state, 2)
        texto += ' '*7
        texto += '  '

        # D
        texto += converter.convert(self.order.mode.bank_id.city, 20)
        texto += ' '

        # E
        texto += ' '*24
        texto += converter.convert(abs(recibo['amount']), 9)
        texto += ' '*15
        texto += datetime.strptime(recibo['ml_maturity_date'],
                                   '%Y-%m-%d').strftime('%d%m%y')
        texto += ' '*(6+6+1+4+16)
        texto += '\r\n'
        if len(texto) != 152:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 150 '
                        'characters long:\n%s') % ('Registro individual I 32',
                                                   texto), True)
        return texto

    @api.model
    def _registro_individual_ii_32(self, recibo):
        converter = self.env['payment.converter.spain']
        # A: Identificacion de la operacion
        texto = '2665'
        texto += '  '

        # B: Datos del efecto
        texto += converter.convert(self.num_recibos+1, 15)
        texto += '  '
        # Recibo
        texto += '2'
        texto += '000000'
        texto += '1'
        # 0= Sin gastos, 1=Con gastos, 9=Orden expresa de protesto notarial
        texto += '0'

        # C: Datos del efecto
        ccc = recibo['bank_id'] and recibo['bank_id'].acc_number or ''
        if ccc:
            texto += ccc[:20].zfill(20)
        else:
            texto += ' '*20

        # D: Datos del efecto
        texto += converter.convert(self.order.mode.partner_id.name, 34)
        texto += converter.convert(recibo['partner_id'].name, 34)
        texto += ' '*30
        texto += '\r\n'
        if len(texto) != 152:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 150 '
                        'characters long:\n%s') % ('Registro individual II 32',
                                                   texto), True)
        return texto

    @api.model
    def _registro_individual_iii_32(self, recibo):
        converter = self.env['payment.converter.spain']
        # A: Identificacion de la operacion
        texto = '2765'
        texto += '  '

        # B: Datos del efecto
        texto += converter.convert(self.num_recibos+1, 15)
        texto += '  '
        partner = self.env['res.partner']
        addresses = partner.address_get([recibo['partner_id'].id])
        address = partner.browse(addresses['default'])
        texto += converter.convert(address.street, 34)
        texto += converter.convert(address.zip, 5)
        texto += converter.convert(address.city, 20)
        address_state = address.state_id and address.state_id.code or False
        texto += converter.convert(address_state, 2)
        texto += '0'*7

        # C: Datos del efecto
        partner_id = recibo['partner_id']
        vat = partner_id.vat and partner_id.vat[2:] or False
        texto += converter.convert(vat, 9)
        texto += ' '*50
        texto += '\r\n'
        if len(texto) != 152:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 150 '
                        'characters long:\n%s') % ('Registro individual III '
                                                   '32', texto), True)
        return texto

    @api.model
    def _registro_fin_remesa_32(self):
        converter = self.env['payment.converter.spain']
        # A: Identificación de la operación
        texto = '7165'
        texto += '  '

        # B: Control de duplicidades
        texto += datetime.today().strftime('%d%m%y')
        texto += '0001'
        texto += ' '*(6+6)

        # C: Libre
        texto += ' '*37

        # D: Acumuladores de importe
        texto += ' '*10
        texto += converter.convert(abs(self.order.total), 10)
        texto += ' '*(10+6+7+6+6+6)

        # E: Controles de lectura de fichero
        texto += ' '*5
        texto += converter.convert((self.num_recibos*3) + 2, 7)
        texto += converter.convert(self.num_recibos, 6)
        texto += ' '*6
        texto += '\r\n'
        if len(texto) != 152:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 150 '
                        'characters long:\n%s') % ('Fin remesa 32', texto),
                      True)
        return texto

    @api.model
    def _registro_fin_fichero_32(self):
        converter = self.env['payment.converter.spain']
        # A: Identificación de la operación
        texto = '9865'
        texto += '  '

        # B: Libre
        texto += ' '*22

        # C: Libre
        texto += ' '*37

        # D: Acumuladores de importes
        texto += ' '*10
        texto += converter.convert(abs(self.order.total), 10)
        texto += ' '*(10+6+7+6+6+6)

        # E: Controles de lectura del fichero
        texto += '00001'
        texto += converter.convert((self.num_recibos*3) + 3, 7)
        texto += converter.convert(self.num_recibos, 6)
        texto += ' '*6
        texto += '\r\n'
        if len(texto) != 152:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 150 '
                        'characters long:\n%s') % ('Fin fichero 32', texto),
                      True)
        return texto

    @api.model
    def create_file(self, order, lines):
        self.order = order

        txt_file = ''
        self.num_recibos = 0
        self.num_lines_opc = 0

        txt_file += self._cabecera_fichero_32()
        txt_file += self._cabecera_remesa_32()
        for recibo in lines:
            txt_file += self._registro_individual_i_32(recibo)
            txt_file += self._registro_individual_ii_32(recibo)
            txt_file += self._registro_individual_iii_32(recibo)
            self.num_recibos = self.num_recibos + 1
        txt_file += self._registro_fin_remesa_32()
        txt_file += self._registro_fin_fichero_32()
        return txt_file
