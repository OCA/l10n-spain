# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2006 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#                       Pedro Tarrafeta <pedro@acysos.com>
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
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
# Rehecho de nuevo para instalación OpenERP 5.0.0 sobre account_payment_extension: Zikzakmedia S.L. 2009
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
from tools.translate import _
from converter import *
import time

csb34_code = {
    'transfer': '56',
    'cheques': '57',
    'promissory_note': '58',
    'certified_payments': '59',
}

class csb_34:

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
                value = unicode(recibo[field],'UTF-8')
            elif type(recibo[field]) == unicode:
                value = recibo[field]
            else:
                value = str(recibo[field])
            message = message.replace('${' + field + '}', value)
        return message

    def _start_34(self, cr, context):
        return convert(cr, self.order.mode.bank_id.partner_id.vat[2:] + self.order.mode.sufijo, 12, context)

    def _cabecera_ordenante_34(self, cr, uid, context):
        today = datetime.today().strftime('%d%m%y')

        text = ''

        # Primer tipo
        text += '0362'
        text += self._start_34(cr, context)
        text += 12*' '
        text += '001'
        text += today
        if self.order.date_scheduled:
            planned = datetime.strptime(self.order.date_scheduled, '%Y-%m-%d')
            text += planned.strftime('%d%m%y')
        else:
            text += today
        #text += self.convert(self.order.mode.nombre, 40)
        text += convert_bank_account(cr, self.order.mode.bank_id.acc_number, self.order.mode.partner_id.name, context)
        text += '0'
        text += 8*' '
        text += '\n'

        # Segundo Tipo
        text += '0362'
        text += self._start_34(cr, context)
        text += 12*' '
        text += '002'
        text += convert(cr, self.order.mode.bank_id.partner_id.name, 36, context)
        text += 5*' '
        text += '\n'

        # Tercer Tipo 
        text += '0362'
        text += self._start_34(cr, context)
        text += 12*' '
        text += '003'
        # Direccion
        address = None
        address_ids = self.pool.get('res.partner').address_get(cr, uid, [self.order.mode.bank_id.partner_id.id], ['invoice', 'default'])
        if address_ids.get('invoice'):
            address = self.pool.get('res.partner.address').read(cr, uid, [address_ids.get('invoice')], ['street','zip','city'], context)[0]
        elif address_ids.get('default'):
            address = self.pool.get('res.partner.address').read(cr, uid, [address_ids.get('default')], ['street','zip','city'], context)[0]
        else:
            raise Log( _('User error:\n\nCompany %s has no invoicing or default address.') % self.order.mode.bank_id.partner_id.name )
        text += convert(cr, address['street'], 36, context)
        text += 5*' '
        text += '\n'

        # Cuarto Tipo 
        text += '0362'
        text += self._start_34(cr, context)
        text += 12*' '
        text += '004'
        text += convert(cr, address['zip'], 6, context)
        text += convert(cr, address['city'], 30, context)
        text += 5*' '
        text += '\n'
    
        return text

    def _cabecera_nacionales_34(self, cr, uid, context):
        text = '0456'
        text += self._start_34(cr, context)
        text += 12*' '
        text += 3*' '
        text += 41*' '
        text += '\n'
        return text

    def _detalle_nacionales_34(self, cr, uid, recibo, csb34_type, context):
    
        address = None
        address_ids = self.pool.get('res.partner').address_get(cr, uid, [recibo['partner_id'].id], ['invoice', 'default'])
        if address_ids.get('invoice'):
            address = self.pool.get('res.partner.address').browse(cr, uid, address_ids.get('invoice'), context)
        elif address_ids.get('default'):
            address = self.pool.get('res.partner.address').browse(cr, uid, address_ids.get('default'), context)
        else:
            raise Log( _('User error:\n\nPartner %s has no invoicing or default address.') % recibo['partner_id'].name )

        # Primer Registro
        text = ''
        text += '06'
        text += csb34_code[csb34_type]
        text += self._start_34(cr, context)
        text += convert(cr, recibo['partner_id'].vat, 12, context)
        text += '010'
        text += convert(cr, abs(recibo['amount']), 12, context)
        #text += convert_bank_account(cr, recibo['bank_id'].acc_number, recibo['partner_id'].name, context)
        ccc = recibo['bank_id'] and recibo['bank_id'].acc_number or ''
        ccc = digits_only(ccc)
        text += ccc[:20].zfill(20)
        text += '1'
        text += '9' # Otros conceptos (ni Nomina ni Pension)
        text += '1'
        text += 6*' '
        text += '\n'

        # Segundo Registro
        text += '06'
        text += csb34_code[csb34_type] 
        text += self._start_34(cr, context)
        text += convert(cr, recibo['partner_id'].vat, 12, context)
        text += '011'
        text += convert(cr, recibo['partner_id'].name, 36, context)
        text += 5*' '
        text += '\n'

        # Tercer y Cuarto Registro
        lines = []
        if address.street:
            lines.append(("012", address.street))
        if address.street2:
            lines.append(("013", address.street2))
        for (code, street) in lines:
            text += '06'
            text += csb34_code[csb34_type] 
            text += self._start_34(cr, context)
            text += convert(cr, recibo['partner_id'].vat, 12, context)
            text += code
            text += convert(cr, street, 36, context)
            text += 5*' '
            text += '\n'

        # Quinto Registro
        if address.zip or address.city:
            text += '06'
            text += csb34_code[csb34_type] 
            text += self._start_34(cr, context)
            text += convert(cr, recibo['partner_id'].vat, 12, context)
            text += '014'
            text += convert(cr, address.zip, 6, context)
            text += convert(cr, address.city, 30, context)
            text += 5*' '
            text += '\n'

        # Si la orden se emite por carta
        if self.order.mode.send_letter:

            # Sexto Registro
            text += '06'
            text += csb34_code[csb34_type] 
            text += self._start_34(cr, context)
            text += convert(cr, recibo['partner_id'].vat, 12, context)
            text += '015'
            country_code = address.country_id and address.country_id.code or ''
            state = address.state_id and address.state_id.name or ''
            text += convert(cr, country_code, 2, context)
            text += convert(cr, state, 34, context)
            text += 5*' '
            text += '\n'

            # Séptimo Registro
            if self.order.mode.payroll_check:
                text += '06'
                text += csb34_code[csb34_type] 
                text += self._start_34(cr, context)
                text += convert(cr, recibo['partner_id'].vat, 12, context)
                text += '018'
                text += convert(cr, recibo['partner_id'].vat, 36, context)
                text += 5*' '
                text += '\n'

            # Registro ciento uno (registro usados por algunos bancos como texto de la carta)
            text += '06'
            text += csb34_code[csb34_type] 
            text += self._start_34(cr, context)
            text += convert(cr, recibo['partner_id'].vat, 12, context)
            text += '101'
            message = self.get_message(recibo, self.order.mode.text1)
            text += convert(cr, message, 36, context)
            text += 5*' '
            text += '\n'

            # Registro ciento dos (registro usados por algunos bancos como texto de la carta)
            text += '06'
            text += csb34_code[csb34_type] 
            text += self._start_34(cr, context)
            text += convert(cr, recibo['partner_id'].vat, 12, context)
            text += '102'
            message = self.get_message(recibo, self.order.mode.text2)
            text += convert(cr, message, 36, context)
            text += 5*' '
            text += '\n'

            # Registro ciento tres (registro usados por algunos bancos como texto de la carta)
            text += '06'
            text += csb34_code[csb34_type] 
            text += self._start_34(cr, context)
            text += convert(cr, recibo['partner_id'].vat, 12, context)
            text += '103'
            message = self.get_message(recibo, self.order.mode.text3)
            text += convert(cr, message, 36, context)
            text += 5*' '
            text += '\n'

            # Registro novecientos diez (registro usados por algunos bancos como fecha de la carta)
            if self.order.mode.add_date:
                if recibo['date']:
                    date = recibo['date']
                elif self.order.date_scheduled:
                    date = self.order.date_scheduled
                else:
                    date = time.strftime('%Y-%m-%d')
                [year,month,day] = date.split('-')
                message = day+month+year
                text += '08'
                text += csb34_code[csb34_type] 
                text += self._start_34(cr, context)
                text += convert(cr, recibo['partner_id'].vat, 12, context)
                text += '910'
                text += convert(cr, message, 36, context)
                text += 5*' '
                text += '\n'

        return text

    def _totales_nacionales_34(self, cr, uid, values, context):
        text = '0856'
        text += self._start_34(cr, context)
        text += 12*' '
        text += 3*' '
        text += convert(cr, self.order.total, 12, context)
        text += convert(cr, values[0], 8, context)
        text += convert(cr, values[1], 10, context)
        text += 6*' '
        text += 5*' '
        text += '\n'
        return text

    def _total_general_34(self, cr, uid, values, context):
        text = '0962'
        text += self._start_34(cr, context)
        text += 12*' '
        text += 3*' '
        text += convert(cr, self.order.total, 12, context)
        text += convert(cr, values[0], 8, context)
        text += convert(cr, values[1], 10, context)
        text += 6*' '
        text += 5*' '
        text += '\n'
        return text

    def create_file(self, pool, cr, uid, order, lines, context):
        self.pool = pool
        self.order = order
        self.context = context

        payment_line_count = 0
        record_count = 0

        file = ''
        file += self._cabecera_ordenante_34(cr, uid, context)
        file += self._cabecera_nacionales_34(cr, uid, context)
        for recibo in lines:
            text = self._detalle_nacionales_34(cr, uid, recibo, order.mode.csb34_type, context)
            file += text
            record_count += len(text.split('\n'))-1
            payment_line_count += 1
        values = (payment_line_count, record_count + 2)
        file += self._totales_nacionales_34(cr, uid, values, context)
        record_count =  len(file.split('\n'))
        values = (payment_line_count, record_count)
        file += self._total_general_34(cr, uid, values, context)
        return file

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
