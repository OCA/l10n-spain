# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2006 ACYSOS S.L. (http://acysos.com)
#                       Pedro Tarrafeta <pedro@acysos.com>
#                       Ignacio Ibeas <ignacio@acysos.com>
#    Copyright (c) 2008 Pablo Rocandio.
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com)
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2009 NaN (http://www.nan-tic.com)
#                       Albert Cervera i Areny <albert@nan-tic.com>
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
# Adaptacion de la norma 34-01 para emision de pagos. Validado para La Caixa:
#   2012 Joan M. Grande <totaler@gmail.com>
#
# Refactorización. Acysos S.L. (http://www.acysos.com) 2012
#   Ignacio Ibeas <ignacio@acysos.com>
#
# Migración Odoo 8.0. Acysos S.L. (http://www.acysos.com) 2015
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

from openerp import _
from datetime import datetime
from .log import Log
from .converter import PaymentConverterSpain


class Csb3401(object):
    def __init__(self, env):
        self.env = env

    def _start_34(self):
        converter = PaymentConverterSpain()
        return converter.convert(self.order.mode.bank_id.partner_id.vat[2:],
                                 10, 'right')

    def _cabecera_ordenante_34(self):
        converter = PaymentConverterSpain()
        today = datetime.today().strftime('%d%m%y')

        text = ''

        # Primer tipo
        text += '0356'
        text += self._start_34()
        text += '34016'
        text += 7*' '
        text += '001'
        text += today
        if self.order.date_scheduled:
            planned = datetime.strptime(self.order.date_scheduled, '%Y-%m-%d')
            text += planned.strftime('%d%m%y')
        else:
            text += today

        ccc = converter.bank_account_parts(self.order.mode.bank_id.acc_number,
                                           self.order.mode.partner_id.name)
        text += ccc['bank']
        text += ccc['office']
        text += ccc['account']
        # Detalle de cargo
        text += '0'
        # Gastos por cuenta del ordenante
        text += '1'
        text += 2*' '
        text += ccc['dc']
        text += 7*' '
        text += '\n'

        # Segundo Tipo
        text += '0356'
        text += self._start_34()
        text += '34016'
        text += 7*' '
        text += '002'
        text += converter.convert(self.order.mode.bank_id.partner_id.name, 36)
        text += 7*' '
        text += '\n'

        # Tercer Tipo
        text += '0356'
        text += self._start_34()
        text += '34016'
        text += 7*' '
        text += '003'
        # Direccion
        partner_model = self.env['res.partner']
        address_id = self.order.mode.bank_id.partner_id.address_get(
            ['invoice'])['invoice']
        if not address_id:
            raise Log(_('User error:\n\nCompany %s has no invoicing '
                        'address.') % address_id)
        address = partner_model.browse(address_id)
        street = address.street
        text += converter.convert(street, 36)
        text += 7*' '
        text += '\n'
        # Cuarto Tipo
        text += '0356'
        text += self._start_34()
        text += '34016'
        text += 7*' '
        text += '004'
        city = address.city
        text += converter.convert(city, 36)
        text += 7*' '
        text += '\n'
        return text

    def _detalle_nacionales_34(self, recibo):
        converter = PaymentConverterSpain()
        # Primer Registro
        text = ''
        text += '0656'
        text += self._start_34()
        if not recibo['partner_id'].vat:
            raise Log(_('User error:\n\nCompany %s has no vat.') %
                      recibo['partner_id'].name)
        text += converter.convert(recibo['partner_id'].vat[2:], 12, 'right')
        text += '010'
        text += converter.convert(recibo['amount'], 12)
        ccc = converter.bank_account_parts(recibo['bank_id'].acc_number,
                                           recibo['partner_id'].name)
        text += ccc['bank']
        text += ccc['office']
        text += ccc['account']
        text += ' '
        # Otros conceptos (ni Nomina ni Pension)
        text += '9'
        text += 2*' '
        text += ccc['dc']
        text += 7*' '
        text += '\n'

        # Segundo Registro
        text += '0656'
        text += self._start_34()
        if not recibo['partner_id'].vat:
            raise Log(_('User error:\n\nCompany %s has no vat.') %
                      recibo['partner_id'].name)
        text += converter.convert(recibo['partner_id'].vat[2:], 12, 'right')
        text += '011'
        text += converter.convert(recibo['partner_id'].name, 36)
        text += 7*' '
        text += '\n'
        return text

    def _totales_nacionales_34(self):
        converter = PaymentConverterSpain()
        text = '0856'
        text += self._start_34()
        text += 12*' '
        text += 3*' '
        text += converter.convert(self.order.total, 12)
        text += converter.convert(self.payment_line_count, 8)
        text += converter.convert(self.record_count, 10)
        text += 6*' '
        text += 7*' '
        text += '\n'
        return text

    def create_file(self, order, lines):
        self.order = order
        self.payment_line_count = 0
        self.record_count = 0
        txt_file = ''
        txt_file += self._cabecera_ordenante_34()
        self.record_count += 4
        for recibo in lines:
            txt_file += self._detalle_nacionales_34(recibo)
            self.payment_line_count += 1
            self.record_count += 2
        self.record_count += 1
        txt_file += self._totales_nacionales_34()
        return txt_file
