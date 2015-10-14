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
import time


class Csb34(models.Model):
    _name = 'csb.34'
    _auto = False

    @api.model
    def get_message(self, recibo, message=None):
        """
        Evaluates an expression and returns its value
        @param recibo: Order line data
        @param message: The expression to be evaluated
        @return: Computed message (string)
        """
        fields = [
            'name',
            'amount',
            'communication',
            'communication2',
            'date',
            'ml_maturity_date',
            'create_date',
            'ml_date_created'
        ]
        if message is None or not message:
            message = ''
        for field in fields:
            if type(recibo[field]) == str:
                value = unicode(recibo[field], 'UTF-8')
            elif type(recibo[field]) == unicode:
                value = recibo[field]
            else:
                value = str(recibo[field])
            message = message.replace('${' + field + '}', value)
        return message

    @api.model
    def _start_34(self):
        converter = self.env['payment.converter.spain']
        vat = self.order.mode.bank_id.partner_id.vat[2:]
        suffix = self.order.mode.csb_suffix
        return converter.convert(vat + suffix, 12)

    @api.model
    def _cabecera_ordenante_34(self):
        converter = self.env['payment.converter.spain']
        today = datetime.today().strftime('%d%m%y')

        text = ''

        # Primer tipo
        text += '0362'
        text += self._start_34()
        text += 12*' '
        text += '001'
        text += today
        if self.order.date_scheduled:
            planned = datetime.strptime(self.order.date_scheduled, '%Y-%m-%d')
            text += planned.strftime('%d%m%y')
        else:
            text += today
        text += converter.convert_bank_account(
            self.order.mode.bank_id.acc_number,
            self.order.mode.partner_id.name)
        text += '0'
        text += 8*' '
        text += '\r\n'

        # Segundo Tipo
        text += '0362'
        text += self._start_34()
        text += 12*' '
        text += '002'
        text += converter.convert(self.order.mode.bank_id.partner_id.name, 36)
        text += 5*' '
        text += '\r\n'

        # Tercer Tipo
        text += '0362'
        text += self._start_34()
        text += 12*' '
        text += '003'
        # Direccion
        address = None
        partner = self.env['res.partner']
        partner_id = self.order.mode.bank_id.partner_id.i
        address_ids = partner.address_get([partner_id], ['invoice', 'default'])
        if address_ids.get('invoice'):
            address = partner.read([address_ids.get('invoice')],
                                   ['street', 'zip', 'city'])[0]
        elif address_ids.get('default'):
            address = partner.read([address_ids.get('default')],
                                   ['street', 'zip', 'city'])[0]
        else:
            raise Log(_('User error:\n\nCompany %s has no invoicing or '
                        'default address.') %
                      self.order.mode.bank_id.partner_id.name)
        text += converter.convert(address['street'], 36)
        text += 5*' '
        text += '\r\n'

        # Cuarto Tipo
        text += '0362'
        text += self._start_34()
        text += 12*' '
        text += '004'
        text += converter.convert(address['zip'], 6)
        text += converter.convert(address['city'], 30)
        text += 5*' '
        text += '\r\n'
        if len(text) % 74 != 0:
            raise Log(_('Configuration error:\n\nA line in "%s" is not 72 '
                        'characters long:\n%s') % ('Cabecera ordenante 34',
                                                   text), True)
        return text

    @api.model
    def _cabecera_nacionales_34(self):
        text = '0456'
        text += self._start_34()
        text += 12*' '
        text += 3*' '
        text += 41*' '
        text += '\r\n'
        if len(text) != 74:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 72 '
                        'characters long:\n%s') % ('Cabecera nacionales 34',
                                                   text), True)
        return text

    @api.model
    def _detalle_nacionales_34(self, recibo, csb34_type):
        converter = self.env['payment.converter.spain']
        csb34_code = {
            'transfer': '56',
            'cheques': '57',
            'promissory_note': '58',
            'certified_payments': '59',
        }
        address = None
        partner = self.env['res.partner']
        address_ids = partner.address_get([recibo['partner_id'].id],
                                          ['invoice', 'default'])
        if address_ids.get('invoice'):
            address = partner.browse(address_ids.get('invoice'))
        elif address_ids.get('default'):
            address = partner.browse(address_ids.get('default'))
        else:
            raise Log(_('User error:\n\nPartner %s has no invoicing or '
                        'default address.') % recibo['partner_id'].name)

        # Primer Registro
        text = ''
        text += '06'
        text += csb34_code[csb34_type]
        text += self._start_34()
        text += converter.convert(recibo['partner_id'].vat, 12)
        text += '010'
        text += converter.convert(abs(recibo['amount']), 12)

        # Si la orden se emite para transferencia
        csb34_type = self.order.mode.csb34_type
        if csb34_type == 'transfer':
            ccc = recibo['bank_id'] and recibo['bank_id'].acc_number or ''
            ccc = converter.digits_only(ccc)
            text += ccc[:20].zfill(20)
        # Si la orden se emite para pagaré, cheque o pago certificado
        else:
            text += 17*'0'
            send_type = self.order.mode.csb34_send_type
            if send_type == 'mail':
                text += '1'
            elif send_type == 'certified_mail':
                text += '2'
            else:
                text += '3'
            if self.order.mode.csb34_not_to_the_order:
                text += '1'
            else:
                text += '0'
            if self.order.mode.csb34_barred:
                text += '9'
            else:
                text += '0'
        if self.order.mode.csb34_cost_key == 'payer':
            text += '1'
        else:
            text += '2'
        concept = self.order.mode.csb34_concept
        if concept == 'payroll':
            text += '1'
        elif concept == 'pension':
            text += '8'
        else:
            text += '9'
        if self.order.mode.csb34_direct_pay_order:
            text += '1'
        else:
            text += '2'
        text += 6*' '
        text += '\r\n'

        # Segundo Registro
        text += '06'
        text += csb34_code[csb34_type]
        text += self._start_34()
        text += converter.convert(recibo['partner_id'].vat, 12)
        text += '011'
        text += converter.convert(recibo['partner_id'].name, 36)
        text += 5*' '
        text += '\r\n'

        # Tercer y Cuarto Registro
        lines = []
        if address.street:
            lines.append(("012", address.street))
        if address.street2:
            lines.append(("013", address.street2))
        for (code, street) in lines:
            text += '06'
            text += csb34_code[csb34_type]
            text += self._start_34()
            text += converter.convert(recibo['partner_id'].vat, 12)
            text += code
            text += converter.convert(street, 36)
            text += 5*' '
            text += '\r\n'

        # Quinto Registro
        if address.zip or address.city:
            text += '06'
            text += csb34_code[csb34_type]
            text += self._start_34()
            text += converter.convert(recibo['partner_id'].vat, 12)
            text += '014'
            text += converter.convert(address.zip, 6)
            text += converter.convert(address.city, 30)
            text += 5*' '
            text += '\r\n'

        # Si la orden se emite por carta (sólo tiene sentido si no son
        # transferencias)
        send_type = self.order.mode.csb34_send_type
        if csb34_type != 'transfer' and (send_type == 'mail' or
                                         send_type == 'certified_mail'):

            # Sexto Registro
            text += '06'
            text += csb34_code[csb34_type]
            text += self._start_34()
            text += converter.convert(recibo['partner_id'].vat, 12)
            text += '015'
            country_code = address.country_id and address.country_id.code or ''
            state = address.state_id and address.state_id.name or ''
            text += converter.convert(country_code, 2)
            text += converter.convert(state, 34)
            text += 5*' '
            text += '\r\n'

            if self.order.mode.csb34_type in ('promissory_note', 'cheques',
                                              'certified_payments'):

                # Séptimo Registro
                if self.order.mode.csb34_payroll_check:
                    text += '06'
                    text += csb34_code[csb34_type]
                    text += self._start_34()
                    text += converter.convert(recibo['partner_id'].vat, 12)
                    text += '018'
                    text += converter.convert(recibo['partner_id'].vat, 36)
                    text += 5*' '
                    text += '\r\n'

                # Registro ciento uno (registro usados por algunos bancos como
                # texto de la carta)
                text += '06'
                text += csb34_code[csb34_type]
                text += self._start_34()
                text += converter.convert(recibo['partner_id'].vat, 12,)
                text += '101'
                message = self.get_message(recibo, self.order.mode.csb34_text1)
                text += converter.convert(message, 36)
                text += 5*' '
                text += '\r\n'

                # Registro ciento dos (registro usados por algunos bancos como
                # texto de la carta)
                text += '06'
                text += csb34_code[csb34_type]
                text += self._start_34()
                text += converter.convert(recibo['partner_id'].vat, 12)
                text += '102'
                message = self.get_message(recibo, self.order.mode.csb34_text2)
                text += converter.convert(message, 36)
                text += 5*' '
                text += '\r\n'

                # Registro ciento tres (registro usados por algunos bancos
                # como texto de la carta)
                text += '06'
                text += csb34_code[csb34_type]
                text += self._start_34()
                text += converter.convert(recibo['partner_id'].vat, 12)
                text += '103'
                message = self.get_message(recibo, self.order.mode.csb34_text3)
                text += converter.convert(message, 36)
                text += 5*' '
                text += '\r\n'

                # Registro novecientos diez (registro usados por algunos bancos
                # como fecha de la carta)
                if self.order.mode.csb34_add_date:
                    if recibo['date']:
                        date = recibo['date']
                    elif self.order.date_scheduled:
                        date = self.order.date_scheduled
                    else:
                        date = time.strftime('%Y-%m-%d')
                    [year, month, day] = date.split('-')
                    message = day+month+year
                    text += '06'
                    text += csb34_code[csb34_type]
                    text += self._start_34()
                    text += converter.convert(recibo['partner_id'].vat, 12)
                    text += '910'
                    text += converter.convert(message, 36)
                    text += 5*' '
                    text += '\r\n'

        if len(text) % 74 != 0:
            raise Log(_('Configuration error:\n\nA line in "%s" is not 72 '
                        'characters long:\n%s') % ('Detalle nacionales 34',
                                                   text), True)
        return text

    @api.model
    def _totales_nacionales_34(self, values):
        converter = self.env['payment.converter.spain']
        text = '0856'
        text += self._start_34()
        text += 12*' '
        text += 3*' '
        text += converter.convert(self.order.total, 12)
        text += converter.convert(values[0], 8)
        text += converter.convert(values[1], 10)
        text += 6*' '
        text += 5*' '
        text += '\r\n'
        if len(text) != 74:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 72 '
                        'characters long:\n%s') % ('Totales nacionales 34',
                                                   text), True)
        return text

    @api.model
    def _total_general_34(self, values):
        converter = self.env['payment.converter.spain']
        text = '0962'
        text += self._start_34()
        text += 12*' '
        text += 3*' '
        text += converter.convert(self.order.total, 12)
        text += converter.convert(values[0], 8)
        text += converter.convert(values[1], 10)
        text += 6*' '
        text += 5*' '
        text += '\r\n'
        if len(text) != 74:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 72 '
                        'characters long:\n%s') % ('Total general 34',
                                                   text), True)
        return text

    @api.model
    def create_file(self, order, lines):
        self.order = order

        payment_line_count = 0
        record_count = 0

        txt_file = ''
        txt_file += self._cabecera_ordenante_34()
        txt_file += self._cabecera_nacionales_34()
        for recibo in lines:
            text = self._detalle_nacionales_34(recibo, order.mode.csb34_type)
            file += text
            record_count += len(text.split('\r\n'))-1
            payment_line_count += 1
        values = (payment_line_count, record_count + 2)
        txt_file += self._totales_nacionales_34(values)
        record_count = len(file.split('\r\n'))
        values = (payment_line_count, record_count)
        txt_file += self._total_general_34(values)
        return txt_file
