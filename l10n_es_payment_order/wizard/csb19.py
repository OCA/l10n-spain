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
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
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
# Añadidos conceptos extras del CSB 19: Acysos S.L. 2011
#   Ignacio Ibeas <ignacio@acysos.com>
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

from openerp import _
from datetime import datetime
from .log import Log
from .converter import PaymentConverterSpain


class Csb19(object):
    def __init__(self, env):
        self.env = env

    def _cabecera_presentador_19(self):
        converter = PaymentConverterSpain()
        text = '5180'
        text += (self.order.mode.bank_id.partner_id.vat[2:] +
                 self.order.mode.csb_suffix).zfill(12)
        text += datetime.today().strftime('%d%m%y')
        text += 6*' '
        text += converter.to_ascii(
            self.order.mode.bank_id.partner_id.name).ljust(40)
        text += 20*' '
        cc = converter.digits_only(self.order.mode.bank_id.acc_number)
        text += cc[0:8]
        text += 66*' '
        text += '\r\n'
        if len(text) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 '
                        'characters long:\n%s') % ('Cabecera presentador 19',
                                                   text), True)
        return text

    def _cabecera_ordenante_19(self, recibo=None):
        converter = PaymentConverterSpain()
        text = '5380'
        text += (self.order.mode.bank_id.partner_id.vat[2:] +
                 self.order.mode.csb_suffix).zfill(12)
        text += datetime.today().strftime('%d%m%y')

        if self.order.date_prefered == 'due':
            assert recibo
            if recibo.get('date'):
                date_cargo = datetime.strptime(recibo['date'], '%Y-%m-%d')
            elif recibo.get('ml_maturity_date'):
                date_cargo = datetime.strptime(recibo['ml_maturity_date'],
                                               '%Y-%m-%d')
            else:
                date_cargo = datetime.today()
        elif self.order.date_prefered == 'now':
            date_cargo = datetime.today()
        else:
            if not self.order.date_scheduled:
                raise Log(_('User error:\n\nFixed date of charge has not been'
                            ' defined.'), True)
            date_cargo = datetime.strptime(self.order.date_scheduled,
                                           '%Y-%m-%d')

        text += date_cargo.strftime('%d%m%y')
        text += converter.to_ascii(
            self.order.mode.bank_id.partner_id.name).ljust(40)
        cc = converter.digits_only(self.order.mode.bank_id.acc_number)
        text += cc[0:20]
        text += 8*' '
        text += '01'
        text += 64*' '
        text += '\r\n'
        if len(text) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 '
                        'characters long:\n%s') % ('Cabecera ordenante 19',
                                                   text), True)
        return text

    def _individual_obligatorio_19(self, recibo):
        converter = PaymentConverterSpain()
        text = '5680'
        text += (self.order.mode.bank_id.partner_id.vat[2:] +
                 self.order.mode.csb_suffix).zfill(12)
        text += str(recibo['name'])[-12:].zfill(12)
        nombre = converter.to_ascii(recibo['partner_id'].name)
        text += nombre[0:40].ljust(40)
        ccc = recibo['bank_id'] and recibo['bank_id'].acc_number or ''
        ccc = converter.digits_only(ccc)
        text += str(ccc)[0:20].zfill(20)
        importe = int(round(abs(recibo['amount'])*100, 0))
        text += str(importe).zfill(10)
        # Referencia para devolución (sólo válida si no se agrupa) #
        if len(recibo['ml_inv_ref']) == 1:
            text += str(recibo['ml_inv_ref'][0].id)[-16:].zfill(16)
        else:
            text += 16*' '

        concepto = ''
        if recibo['communication']:
            concepto = recibo['communication']
        text += converter.to_ascii(concepto)[0:48].ljust(48)
        text += '\r\n'
        if len(text) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 '
                        'characters long:\n%s') % ('Individual obligatorio 19',
                                                   text), True)
        return text

    def _individual_opcional_19(self, recibo):
        """Para poner el segundo text de comunicación (en lugar de nombre, '
        'domicilio y localidad opcional)"""
        converter = PaymentConverterSpain()
        text = '5686'
        text += (self.order.mode.bank_id.partner_id.vat[2:] +
                 self.order.mode.csb_suffix).zfill(12)
        text += str(recibo['name'])[-12:].zfill(12)
        text += converter.to_ascii(recibo['communication2'])[0:115].ljust(115)
        text += '00000'
        text += 14*' '
        text += '\r\n'
        if len(text) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 '
                        'characters long:\n%s') % ('Individual opcional 19',
                                                   text), True)
        return text

    def _extra_opcional_19(self, recibo):
        """Para poner los 15 conceptos opcional de los registros 5681-5685 '
        'utilizando las lineas de facturación (Máximo 15 lineas)"""
        converter = PaymentConverterSpain()
        res = {}
        res['text'] = ''
        res['total_lines'] = 0
        counter = 1
        registry_counter = 1
        length = 0
        for invoice in recibo['ml_inv_ref']:
            if invoice:
                length += len(invoice.invoice_line)
        for invoice in recibo['ml_inv_ref']:
            if invoice:
                for invoice_line in invoice.invoice_line:
                    if counter <= length:
                        if counter <= 15:
                            if (counter-1) % 3 == 0:
                                res['text'] += '568'+str(registry_counter)
                                partner = self.order.mode.bank_id.partner_id
                                res['text'] += (
                                    partner.vat[2:] +
                                    self.order.mode.csb_suffix).zfill(12)
                                res['text'] += str(recibo['name']).zfill(12)
                            price = ' %(#).2f ' % {
                                '#': invoice_line.price_subtotal}
                            res['text'] += converter.to_ascii(
                                invoice_line.name)[0:(40-len(price))].ljust(
                                40-len(price))
                            res['text'] += converter.to_ascii(
                                price.replace('.', ','))
                            if counter % 3 == 0:
                                res['text'] += 14*' '+'\r\n'
                                res['total_lines'] += 1
                                if len(res['text']) != registry_counter*164:
                                    raise Log(_('Configuration error:\n\nThe '
                                                'line "%s" is not 162 '
                                                'characters long:\n%s') % (
                                        'Individual opcional 19',
                                        res['text']), True)
                                registry_counter += 1
                            elif counter == length:
                                tmp_txt = (3 - (counter % 3)) * 40 * ' '
                                tmp_txt += 14 * ' ' + '\r\n'
                                res['text'] += tmp_txt
                                res['total_lines'] += 1
                                if len(res['text']) != registry_counter*164:
                                    raise Log(_('Configuration error:\n\nThe '
                                                'line "%s" is not 162 '
                                                'characters long:\n%s') % (
                                        'Individual opcional 19',
                                        res['text']), True)
                            counter += 1
        return res

    def _total_ordenante_19(self):
        text = '5880'
        text += (self.order.mode.bank_id.partner_id.vat[2:] +
                 self.order.mode.csb_suffix).zfill(12)
        text += 72*' '
        totalordenante = int(round(abs(self.group_amount) * 100, 0))
        text += str(totalordenante).zfill(10)
        text += 6*' '
        text += str(self.group_payments).zfill(10)
        text += str(self.group_payments +
                    self.group_optional_lines + 2).zfill(10)
        text += 38*' '
        text += '\r\n'
        if len(text) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 '
                        'characters long:\n%s') % ('Total ordenante 19',
                                                   text), True)
        return text

    def _total_general_19(self):
        text = '5980'
        text += (self.order.mode.bank_id.partner_id.vat[2:] +
                 self.order.mode.csb_suffix).zfill(12)
        text += 52*' '
        if self.order.date_prefered == 'due':
            # Tantos ordenantes como pagos
            text += str(self.total_payments).zfill(4)
        else:
            # Sólo un ordenante
            text += '0001'
        text += 16*' '
        totalremesa = int(round(abs(self.order.total) * 100, 0))
        text += str(totalremesa).zfill(10)
        text += 6*' '
        text += str(self.total_payments).zfill(10)
        if self.order.date_prefered == 'due':
            # Tantos ordenantes como pagos
            text += str(self.total_payments*3 +
                        self.total_optional_lines + 2).zfill(10)
        else:
            # Sólo un ordenante
            text += str(self.total_payments +
                        self.total_optional_lines + 4).zfill(10)
        text += 38*' '
        text += '\r\n'
        if len(text) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 '
                        'characters long:\n%s') % ('Total general 19', text),
                      True)
        return text

    def create_file(self, order, lines):
        self.order = order

        txt_file = ''
        self.total_payments = 0
        self.total_optional_lines = 0
        self.group_payments = 0
        self.group_optional_lines = 0
        self.group_amount = 0.0

        txt_file += self._cabecera_presentador_19()

        if order.date_prefered == 'due':
            # Tantos ordenantes como pagos
            for recibo in lines:
                self.group_payments = 0
                self.group_optional_lines = 0
                self.group_amount = 0.0

                txt_file += self._cabecera_ordenante_19(recibo)
                txt_file += self._individual_obligatorio_19(recibo)
                self.total_payments += 1
                self.group_payments += 1
                self.group_amount += abs(recibo['amount'])
                if order.mode.csb19_extra_concepts:
                    extra_concepts = self._extra_opcional_19(recibo)
                    txt_file += extra_concepts['text']
                    self.total_optional_lines += extra_concepts['total_lines']
                    self.group_optional_lines += extra_concepts['total_lines']

                if recibo['communication2']:
                    txt_file += self._individual_opcional_19(recibo)
                    self.total_optional_lines += 1
                    self.group_optional_lines += 1
                txt_file += self._total_ordenante_19()
        else:
            # Sólo un ordenante
            txt_file += self._cabecera_ordenante_19()
            self.group_payments = 0
            self.group_optional_lines = 0
            self.group_amount = 0.0

            for recibo in lines:
                txt_file += self._individual_obligatorio_19(recibo)
                self.total_payments += 1
                self.group_payments += 1
                self.group_amount += abs(recibo['amount'])
                if order.mode.csb19_extra_concepts:
                    extra_concepts = self._extra_opcional_19(recibo)
                    txt_file += extra_concepts['text']
                    self.total_optional_lines += extra_concepts['total_lines']
                    self.group_optional_lines += extra_concepts['total_lines']
                if recibo['communication2']:
                    txt_file += self._individual_opcional_19(recibo)
                    self.total_optional_lines += 1
                    self.group_optional_lines += 1

            txt_file += self._total_ordenante_19()

        txt_file += self._total_general_19()
        return txt_file
