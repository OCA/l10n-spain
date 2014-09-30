# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2006 ACYSOS S.L. (http://acysos.com)
#                       Pedro Tarrafeta <pedro@acysos.com>
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
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
from log import Log
import time


class Csb34(orm.Model):
    _name = 'csb.34'
    _auto = False

    def get_message(self, cr, uid, recibo, message=None):
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

    def _start_34(self, cr, uid, context):
        converter = self.pool.get('payment.converter.spain')
        return converter.convert(
            cr, uid, self.order.mode.bank_id.partner_id.vat[2:] +
            self.order.mode.sufijo, 12, context)

    def _cabecera_ordenante_34(self, cr, uid, context):
        converter = self.pool['payment.converter.spain']
        today = datetime.today().strftime('%d%m%y')
        text = ''
        # Primer tipo
        text += '0362'
        text += self._start_34(cr, uid, context)
        text += 12*' '
        text += '001'
        text += today
        if self.order.date_scheduled:
            planned = datetime.strptime(self.order.date_scheduled, '%Y-%m-%d')
            text += planned.strftime('%d%m%y')
        else:
            text += today
        text += converter.convert_bank_account(
            cr, uid, self.order.mode.bank_id.acc_number,
            self.order.mode.partner_id.name, context)
        text += '0'
        text += 8*' '
        text += '\r\n'
        # Segundo Tipo
        text += '0362'
        text += self._start_34(cr, uid, context)
        text += 12*' '
        text += '002'
        text += converter.convert(
            cr, uid, self.order.mode.bank_id.partner_id.name, 36, context)
        text += 5*' '
        text += '\r\n'
        # Tercer Tipo
        text += '0362'
        text += self._start_34(cr, uid, context)
        text += 12*' '
        text += '003'
        # Direccion
        address = None
        address_ids = self.pool['res.partner'].address_get(
            cr, uid, [self.order.mode.bank_id.partner_id.id],
            ['invoice', 'default'])
        if address_ids.get('invoice'):
            address = self.pool['res.partner'].read(
                cr, uid, [address_ids.get('invoice')], ['street', 'zip',
                                                        'city'],
                context)[0]
        elif address_ids.get('default'):
            address = self.pool['res.partner'].read(
                cr, uid, [address_ids.get('default')], ['street', 'zip',
                                                        'city'],
                context)[0]
        else:
            raise Log(_('User error:\n\nCompany %s has no invoicing or '
                        'default address.') %
                      self.order.mode.bank_id.partner_id.name)
        text += converter.convert(cr, uid, address['street'], 36, context)
        text += 5*' '
        text += '\r\n'
        # Cuarto Tipo
        text += '0362'
        text += self._start_34(cr, uid, context)
        text += 12*' '
        text += '004'
        text += converter.convert(cr, uid, address['zip'], 6, context)
        text += converter.convert(cr, uid, address['city'], 30, context)
        text += 5*' '
        text += '\r\n'
        if len(text) % 74 != 0:
            raise Log(_('Configuration error:\n\nA line in "%s" is not 72 '
                        'characters long:\n%s') %
                      ('Cabecera ordenante 34', text), True)
        return text

    def _cabecera_nacionales_34(self, cr, uid, context):
        text = '0456'
        text += self._start_34(cr, uid, context)
        text += 12*' '
        text += 3*' '
        text += 41*' '
        text += '\r\n'
        if len(text) != 74:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 72 '
                        'characters long:\n%s') %
                      ('Cabecera nacionales 34', text), True)
        return text

    def _detalle_nacionales_34(self, cr, uid, recibo, csb34_type, context):
        converter = self.pool['payment.converter.spain']
        csb34_code = {
            'transfer': '56',
            'cheques': '57',
            'promissory_note': '58',
            'certified_payments': '59',
        }
        address = None
        address_ids = self.pool['res.partner'].address_get(
            cr, uid, [recibo['partner_id'].id], ['invoice', 'default'])
        if address_ids.get('invoice'):
            address = self.pool['res.partner'].browse(
                cr, uid, address_ids.get('invoice'), context)
        elif address_ids.get('default'):
            address = self.pool['res.partner'].browse(
                cr, uid, address_ids.get('default'), context)
        else:
            raise Log(_('User error:\n\nPartner %s has no invoicing or '
                        'default address.') % recibo['partner_id'].name)
        # Primer Registro
        text = ''
        text += '06'
        text += csb34_code[csb34_type]
        text += self._start_34(cr, uid, context)
        text += converter.convert(cr, uid, recibo['partner_id'].vat, 12,
                                  context)
        text += '010'
        text += converter.convert(cr, uid, abs(recibo['amount']), 12, context)
        # Si la orden se emite para transferencia
        csb34_type = self.order.mode.csb34_type
        if csb34_type == 'transfer':
            ccc = recibo['bank_id'] and recibo['bank_id'].acc_number or ''
            ccc = converter.digits_only(cr, uid, ccc)
            text += ccc[:20].zfill(20)
        # Si la orden se emite para pagaré, cheque o pago certificado
        else:
            text += 17*'0'
            send_type = self.order.mode.send_type
            if send_type == 'mail':
                text += '1'
            elif send_type == 'certified_mail':
                text += '2'
            else:
                text += '3'
            if self.order.mode.not_to_the_order:
                text += '1'
            else:
                text += '0'
            if self.order.mode.barred:
                text += '9'
            else:
                text += '0'
        if self.order.mode.cost_key == 'payer':
            text += '1'
        else:
            text += '2'
        concept = self.order.mode.concept
        if concept == 'payroll':
            text += '1'
        elif concept == 'pension':
            text += '8'
        else:
            text += '9'
        if self.order.mode.direct_pay_order:
            text += '1'
        else:
            text += '2'
        text += 6*' '
        text += '\r\n'
        # Segundo Registro
        text += '06'
        text += csb34_code[csb34_type]
        text += self._start_34(cr, uid, context)
        text += converter.convert(cr, uid, recibo['partner_id'].vat, 12,
                                  context)
        text += '011'
        text += converter.convert(cr, uid, recibo['partner_id'].name, 36,
                                  context)
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
            text += self._start_34(cr, uid, context)
            text += converter.convert(cr, uid, recibo['partner_id'].vat, 12,
                                      context)
            text += code
            text += converter.convert(cr, uid, street, 36, context)
            text += 5*' '
            text += '\r\n'

        # Quinto Registro
        if address.zip or address.city:
            text += '06'
            text += csb34_code[csb34_type]
            text += self._start_34(cr, uid, context)
            text += converter.convert(cr, uid, recibo['partner_id'].vat, 12,
                                      context)
            text += '014'
            text += converter.convert(cr, uid, address.zip, 6, context)
            text += converter.convert(cr, uid, address.city, 30, context)
            text += 5*' '
            text += '\r\n'

        # Si la orden se emite por carta (sólo tiene sentido si no son
        # transferencias)
        send_type = self.order.mode.send_type
        if (csb34_type != 'transfer' and
                (send_type == 'mail' or send_type == 'certified_mail')):
            # Sexto Registro
            text += '06'
            text += csb34_code[csb34_type]
            text += self._start_34(cr, uid, context)
            text += converter.convert(cr, uid, recibo['partner_id'].vat, 12,
                                      context)
            text += '015'
            country_code = address.country_id and address.country_id.code or ''
            state = address.state_id and address.state_id.name or ''
            text += converter.convert(cr, uid, country_code, 2, context)
            text += converter.convert(cr, uid, state, 34, context)
            text += 5*' '
            text += '\r\n'

            if self.order.mode.csb34_type in ('promissory_note', 'cheques',
                                              'certified_payments'):
                # Séptimo Registro
                if self.order.mode.payroll_check:
                    text += '06'
                    text += csb34_code[csb34_type]
                    text += self._start_34(cr, uid, context)
                    text += converter.convert(
                        cr, uid, recibo['partner_id'].vat, 12, context)
                    text += '018'
                    text += converter.convert(
                        cr, uid, recibo['partner_id'].vat, 36, context)
                    text += 5*' '
                    text += '\r\n'
                # Registro ciento uno (registro usados por algunos bancos como
                # texto de la carta)
                text += '06'
                text += csb34_code[csb34_type]
                text += self._start_34(cr, uid, context)
                text += converter.convert(
                    cr, uid, recibo['partner_id'].vat, 12, context)
                text += '101'
                message = self.get_message(
                    cr, uid, recibo, self.order.mode.text1)
                text += converter.convert(cr, uid, message, 36, context)
                text += 5*' '
                text += '\r\n'
                # Registro ciento dos (registro usados por algunos bancos como
                # texto de la carta)
                text += '06'
                text += csb34_code[csb34_type]
                text += self._start_34(cr, uid, context)
                text += converter.convert(
                    cr, uid, recibo['partner_id'].vat, 12, context)
                text += '102'
                message = self.get_message(
                    cr, uid, recibo, self.order.mode.text2)
                text += converter.convert(cr, uid, message, 36, context)
                text += 5*' '
                text += '\r\n'
                # Registro ciento tres (registro usados por algunos bancos como
                # texto de la carta)
                text += '06'
                text += csb34_code[csb34_type]
                text += self._start_34(cr, uid, context)
                text += converter.convert(
                    cr, uid, recibo['partner_id'].vat, 12, context)
                text += '103'
                message = self.get_message(
                    cr, uid, recibo, self.order.mode.text3)
                text += converter.convert(cr, uid, message, 36, context)
                text += 5*' '
                text += '\r\n'
                # Registro novecientos diez (registro usados por algunos bancos
                # como fecha de la carta)
                if self.order.mode.add_date:
                    if recibo['date']:
                        date = recibo['date']
                    elif self.order.date_scheduled:
                        date = self.order.date_scheduled
                    else:
                        date = time.strftime('%Y-%m-%d')
                    [year, month, day] = date.split('-')
                    message = day + month + year
                    text += '06'
                    text += csb34_code[csb34_type]
                    text += self._start_34(cr, uid, context)
                    text += converter.convert(
                        cr, uid, recibo['partner_id'].vat, 12, context)
                    text += '910'
                    text += converter.convert(cr, uid, message, 36, context)
                    text += 5*' '
                    text += '\r\n'
        if len(text) % 74 != 0:
            raise Log(_('Configuration error:\n\nA line in "%s" is not 72 '
                        'characters long:\n%s') %
                      ('Detalle nacionales 34', text), True)
        return text

    def _totales_nacionales_34(self, cr, uid, values, context):
        converter = self.pool.get('payment.converter.spain')
        text = '0856'
        text += self._start_34(cr, uid, context)
        text += 12*' '
        text += 3*' '
        text += converter.convert(cr, uid, self.order.total, 12, context)
        text += converter.convert(cr, uid, values[0], 8, context)
        text += converter.convert(cr, uid, values[1], 10, context)
        text += 6*' '
        text += 5*' '
        text += '\r\n'
        if len(text) != 74:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 72 '
                        'characters long:\n%s') %
                      ('Totales nacionales 34', text), True)
        return text

    def _total_general_34(self, cr, uid, values, context):
        converter = self.pool['payment.converter.spain']
        text = '0962'
        text += self._start_34(cr, uid, context)
        text += 12*' '
        text += 3*' '
        text += converter.convert(cr, uid, self.order.total, 12, context)
        text += converter.convert(cr, uid, values[0], 8, context)
        text += converter.convert(cr, uid, values[1], 10, context)
        text += 6*' '
        text += 5*' '
        text += '\r\n'
        if len(text) != 74:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 72 '
                        'characters long:\n%s') %
                      ('Total general 34', text), True)
        return text

    def create_file(self, cr, uid, order, lines, context):
        self.order = order
        payment_line_count = 0
        record_count = 0
        file = ''
        file += self._cabecera_ordenante_34(cr, uid, context)
        file += self._cabecera_nacionales_34(cr, uid, context)
        for recibo in lines:
            text = self._detalle_nacionales_34(
                cr, uid, recibo, order.mode.csb34_type, context)
            file += text
            record_count += len(text.split('\r\n'))-1
            payment_line_count += 1
        values = (payment_line_count, record_count + 2)
        file += self._totales_nacionales_34(cr, uid, values, context)
        record_count = len(file.split('\r\n'))
        values = (payment_line_count, record_count)
        file += self._total_general_34(cr, uid, values, context)
        return file
