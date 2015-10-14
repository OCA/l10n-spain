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
#    Copyright (c) 2009 NaN (http://www.nan-tic.com) All Rights Reserved.
#                       Albert Cervera i Areny <albert@nan-tic.com>
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

from openerp import models, api, _
from datetime import datetime
from log import *


class Csb3401(models.Model):
    _name = 'csb.3401'
    _auto = False

    @api.model
    def _start_34(self):
        converter = self.env['payment.converter.spain']
        return converter.convert(self.order.mode.bank_id.partner_id.vat[2:],
                                 10, 'right')

    @api.model
    def _cabecera_ordenante_34(self):
        converter = self.env['payment.converter.spain']
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
        partner = self.env['res.partner']
        address_id = partner.address_get(
            [self.order.mode.bank_id.partner_id.id], ['invoice'])['invoice']
        if not address_id:
            raise Log(_('User error:\n\nCompany %s has no invoicing '
                        'address.') % address_id)

        street = partner.read([address_id], ['street'])[0]['street']
        text += converter.convert(street, 36)
        text += 7*' '
        text += '\n'

        # Cuarto Tipo
        text += '0356'
        text += self._start_34()
        text += '34016'
        text += 7*' '
        text += '004'
        city = partner.read([address_id], ['city'])[0]['city']
        text += converter.convert(city, 36)
        text += 7*' '
        text += '\n'
        return text

    @api.model
    def _detalle_nacionales_34(self, recibo):
        converter = self.env['payment.converter.spain']
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

    @api.model
    def _totales_nacionales_34(self):
        converter = self.env['payment.converter.spain']
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

    def create_file(self, cr, uid, order, lines, context):
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
