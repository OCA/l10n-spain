# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2006 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#                       Pedro Tarrafeta <pedro@acysos.com>
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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
# Añadidos conceptos extras del CSB 19: Acysos S.L. 2011
#   Ignacio Ibeas <ignacio@acysos.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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

from datetime import datetime
from tools.translate import _
from converter import *


class csb_19:
    def _cabecera_presentador_19(self):
        texto = '5180'
        texto += (self.order.mode.bank_id.partner_id.vat[2:] + self.order.mode.sufijo).zfill(12)
        texto += datetime.today().strftime('%d%m%y')
        texto += 6*' '
        texto += to_ascii(self.order.mode.nombre).ljust(40)
        texto += 20*' '
        cc = digits_only(self.order.mode.bank_id.acc_number)
        texto += cc[0:8]
        texto += 66*' '
        texto += '\r\n'
        if len(texto) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 characters long:\n%s') % ('Cabecera presentador 19', texto), True)
        return texto

    def _cabecera_ordenante_19(self, recibo=None):
        texto = '5380'
        texto += (self.order.mode.bank_id.partner_id.vat[2:] + self.order.mode.sufijo).zfill(12)
        texto += datetime.today().strftime('%d%m%y')

        if self.order.date_prefered == 'due':
            assert recibo
            if recibo.get('date'):
                date_cargo = datetime.strptime(recibo['date'],'%Y-%m-%d')
            elif recibo.get('ml_maturity_date'):
                date_cargo = datetime.strptime(recibo['ml_maturity_date'],'%Y-%m-%d')
            else:
                date_cargo = datetime.today()
        elif self.order.date_prefered == 'now':
            date_cargo = datetime.today()
        else: # self.order.date_prefered == 'fixed'
            if not self.order.date_scheduled:
                raise Log(_('User error:\n\nFixed date of charge has not been defined.'), True)
            date_cargo = datetime.strptime(self.order.date_scheduled,'%Y-%m-%d')

        texto += date_cargo.strftime('%d%m%y')
        texto += to_ascii(self.order.mode.nombre).ljust(40)
        cc = digits_only(self.order.mode.bank_id.acc_number)
        texto += cc[0:20]
        texto += 8*' '
        texto += '01'
        texto += 64*' '
        texto += '\r\n'
        if len(texto) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 characters long:\n%s') % ('Cabecera ordenante 19', texto), True)
        return texto

    def _individual_obligatorio_19(self, recibo):
        texto = '5680'
        texto += (self.order.mode.bank_id.partner_id.vat[2:] + self.order.mode.sufijo).zfill(12)
        texto += str(recibo['name'])[-12:].zfill(12)
        nombre = to_ascii(recibo['partner_id'].name)
        texto += nombre[0:40].ljust(40)
        ccc = recibo['bank_id'] and recibo['bank_id'].acc_number or ''
        ccc = digits_only(ccc)
        texto += str(ccc)[0:20].zfill(20)
        importe = int(round(abs(recibo['amount'])*100,0))
        texto += str(importe).zfill(10)
        texto += 16*' '
        concepto = ''
        if recibo['communication']:
            concepto = recibo['communication']
        texto += to_ascii(concepto)[0:48].ljust(48)
        # Esto es lo convencional, descripción de 40 caracteres, pero se puede aprovechar los 8 espacios en blanco finales
        #texto += to_ascii(concepto)[0:40].ljust(40)
        #texto += 8*' '
        texto += '\r\n'
        if len(texto) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 characters long:\n%s') % ('Individual obligatorio 19', texto), True)
        return texto

    def _individual_opcional_19(self, recibo):
        """Para poner el segundo texto de comunicación (en lugar de nombre, domicilio y localidad opcional)"""
        texto = '5686'
        texto += (self.order.mode.bank_id.partner_id.vat[2:] + self.order.mode.sufijo).zfill(12)
        texto += str(recibo['name'])[-12:].zfill(12)
        texto += to_ascii(recibo['communication2'])[0:115].ljust(115)
        texto += '00000' # Campo de código postal ficticio
        texto += 14*' '
        texto += '\r\n'
        if len(texto) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 characters long:\n%s') % ('Individual opcional 19', texto), True)
        return texto

    def _extra_opcional_19(self, recibo):
        """Para poner los 15 conceptos opcional de los registros 5681-5685 utilizando las lineas de facturación (Máximo 15 lineas)"""
        res = {}
        res['texto'] = ''
        res['total_lines'] = 0
        counter = 1
        registry_counter = 1
        lenght = 0
        for invoice in recibo['ml_inv_ref']:
            lenght += len(invoice.invoice_line)
        for invoice in recibo['ml_inv_ref']:
            for invoice_line in invoice.invoice_line:
                if counter <= lenght:
                    if counter <= 15:
                        if (counter-1)%3 == 0:
                            res['texto'] += '568'+str(registry_counter)
                            res['texto'] += (self.order.mode.bank_id.partner_id.vat[2:] + self.order.mode.sufijo).zfill(12)
                            res['texto'] += str(recibo['name']).zfill(12)
                        price = ' %(#).2f ' % {'#' : invoice_line.price_subtotal}
                        res['texto'] += to_ascii(invoice_line.name)[0:(40-len(price))].ljust(40-len(price))
                        res['texto'] += to_ascii(price.replace('.',','))
                        if counter % 3 == 0:
                            res['texto'] += 14*' '+'\r\n'
                            res['total_lines'] += 1
                            if len(res['texto']) != registry_counter*164:
                                raise Log(_('Configuration error:\n\nThe line "%s" is not 162 characters long:\n%s') % ('Individual opcional 19', res['texto']), True)
                            registry_counter += 1
                        elif counter == lenght:
                            res['texto'] += (3-(counter % 3))*40*' '+14*' '+'\r\n'
                            res['total_lines'] += 1
                            if len(res['texto']) != registry_counter*164:
                                raise Log(_('Configuration error:\n\nThe line "%s" is not 162 characters long:\n%s') % ('Individual opcional 19', res['texto']), True)
                        counter += 1
        return res

    def _total_ordenante_19(self):
        texto = '5880'
        texto += (self.order.mode.bank_id.partner_id.vat[2:] + self.order.mode.sufijo).zfill(12)
        texto += 72*' '
        totalordenante = int(round(abs(self.group_amount) * 100,0))
        texto += str(totalordenante).zfill(10)
        texto += 6*' '
        texto += str(self.group_payments).zfill(10)
        texto += str(self.group_payments + self.group_optional_lines + 2).zfill(10)
        texto += 38*' '
        texto += '\r\n'
        if len(texto) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 characters long:\n%s') % ('Total ordenante 19', texto), True)
        return texto

    def _total_general_19(self):
        texto = '5980'
        texto += (self.order.mode.bank_id.partner_id.vat[2:] + self.order.mode.sufijo).zfill(12)
        texto += 52*' '
        if self.order.date_prefered == 'due':
            # Tantos ordenantes como pagos
            texto += str(self.total_payments).zfill(4)
        else:
            # Sólo un ordenante
            texto += '0001'
        texto += 16*' '
        totalremesa = int(round(abs(self.order.total) * 100,0))
        texto += str(totalremesa).zfill(10)
        texto += 6*' '
        texto += str(self.total_payments).zfill(10)
        if self.order.date_prefered == 'due':
            # Tantos ordenantes como pagos
            texto += str(self.total_payments*3 + self.total_optional_lines + 2).zfill(10)
        else:
            # Sólo un ordenante
            texto += str(self.total_payments + self.total_optional_lines + 4).zfill(10)
        texto += 38*' '
        texto += '\r\n'
        if len(texto) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 characters long:\n%s') % ('Total general 19', texto), True)
        return texto


    def create_file(self, pool, cr, uid, order, lines, context):
        self.order = order

        txt_remesa = ''
        self.total_payments = 0
        self.total_optional_lines = 0
        self.group_payments = 0
        self.group_optional_lines = 0
        self.group_amount = 0.0

        txt_remesa += self._cabecera_presentador_19()

        if order.date_prefered == 'due':
            # Tantos ordenantes como pagos
            for recibo in lines:
                self.group_payments = 0
                self.group_optional_lines = 0
                self.group_amount = 0.0

                txt_remesa += self._cabecera_ordenante_19(recibo)
                txt_remesa += self._individual_obligatorio_19(recibo)
                self.total_payments += 1
                self.group_payments += 1
                self.group_amount += abs( recibo['amount'] )
                if order.mode.csb19_extra_concepts:
                    extra_concepts = self._extra_opcional_19(recibo)
                    txt_remesa += extra_concepts['texto']
                    self.total_optional_lines += extra_concepts['total_lines']
                    self.group_optional_lines += extra_concepts['total_lines']

                if recibo['communication2']:
                    txt_remesa += self._individual_opcional_19(recibo)
                    #self.num_lineas_opc = self.num_lineas_opc + 1
                    self.total_optional_lines += 1
                    self.group_optional_lines += 1
                txt_remesa += self._total_ordenante_19()
        else:
            # Sólo un ordenante
            txt_remesa += self._cabecera_ordenante_19()
            self.group_payments = 0
            self.group_optional_lines = 0
            self.group_amount = 0.0

            for recibo in lines:
                txt_remesa += self._individual_obligatorio_19(recibo)
                self.total_payments += 1
                self.group_payments += 1
                self.group_amount += abs( recibo['amount'] )
                if order.mode.csb19_extra_concepts:
                    extra_concepts = self._extra_opcional_19(recibo)
                    txt_remesa += extra_concepts['texto']
                    self.total_optional_lines += extra_concepts['total_lines']
                    self.group_optional_lines += extra_concepts['total_lines']
                if recibo['communication2']:
                    txt_remesa += self._individual_opcional_19(recibo)
                    self.total_optional_lines += 1
                    self.group_optional_lines += 1

            txt_remesa += self._total_ordenante_19()

        txt_remesa += self._total_general_19()
        return txt_remesa

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
