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


class Csb58(models.Model):
    _name = 'csb.58'
    _auto = False

    @api.model
    def _cabecera_presentador_58(self):
        converter = self.env['payment.converter.spain']
        texto = '5170'
        texto += (self.order.mode.bank_id.partner_id.vat[2:] +
                  self.order.mode.csb_suffix).zfill(12)
        texto += datetime.today().strftime('%d%m%y')
        texto += 6*' '
        texto += converter.to_ascii(
            self.order.mode.bank_id.partner_id.name).ljust(40)
        texto += 20*' '
        cc = converter.digits_only(self.order.mode.bank_id.acc_number)
        texto += cc[0:8]
        texto += 66*' '
        texto += '\r\n'
        if len(texto) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 '
                        'characters long:\n%s') % ('Cabecera presentador 58',
                                                   texto), True)
        return texto

    @api.model
    def _cabecera_ordenante_58(self):
        converter = self.env['payment.converter.spain']
        texto = '5370'
        texto += (self.order.mode.bank_id.partner_id.vat[2:] +
                  self.order.mode.csb_suffix).zfill(12)
        texto += datetime.today().strftime('%d%m%y')
        texto += 6*' '
        texto += converter.to_ascii(
            self.order.mode.bank_id.partner_id.name).ljust(40)
        cc = converter.digits_only(self.order.mode.bank_id.acc_number)
        texto += cc[0:20]
        texto += 8*' '
        texto += '06'
        texto += 52*' '
        texto += self.order.mode.csb58_ine and converter.to_ascii(
            self.order.mode.csb58_ine)[:9].zfill(9) or 9*' '
        texto += 3*' '
        texto += '\r\n'
        if len(texto) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 '
                        'characters long:\n%s') % ('Cabecera ordenante 58',
                                                   texto), True)
        return texto

    @api.model
    def _individual_obligatorio_58(self, recibo):
        converter = self.env['payment.converter.spain']
        texto = '5670'
        texto += (self.order.mode.bank_id.partner_id.vat[2:] +
                  self.order.mode.csb_suffix).zfill(12)
        texto += str(recibo['name'])[-12:].zfill(12)
        nombre = converter.to_ascii(recibo['partner_id'].name)
        texto += nombre[0:40].ljust(40)
        ccc = recibo['bank_id'] and recibo['bank_id'].acc_number or ''
        ccc = converter.digits_only(ccc)
        texto += str(ccc)[0:20].zfill(20)
        importe = int(round(abs(recibo['amount'])*100, 0))
        texto += str(importe).zfill(10)
        # Referencia para devolución (sólo válida si no se agrupa) #
        if len(recibo['ml_inv_ref']) == 1:
            texto += str(recibo['ml_inv_ref'][0].id)[-16:].zfill(16)
        else:
            texto += 16*' '
        ######################################################################
        concepto = ''
        if recibo['communication']:
            concepto = recibo['communication']
        texto += converter.to_ascii(concepto)[0:40].ljust(40)
        if recibo.get('date'):
            date_cargo = datetime.strptime(recibo['date'], '%Y-%m-%d')
        elif recibo.get('ml_maturity_date'):
            date_cargo = datetime.strptime(recibo['ml_maturity_date'],
                                           '%Y-%m-%d')
        else:
            date_cargo = datetime.today()
        texto += date_cargo.strftime('%d%m%y')
        texto += 2*' '
        texto += '\r\n'
        if len(texto) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 '
                        'characters long:\n%s') % ('Individual obligatorio 58',
                                                   texto), True)
        return texto

    def _individual_opcional_58(self, cr, uid, recibo):
        """Para poner el segundo texto de comunicación"""
        converter = self.env['payment.converter.spain']
        texto = '5671'
        texto += (self.order.mode.bank_id.partner_id.vat[2:] +
                  self.order.mode.csb_suffix).zfill(12)
        texto += str(recibo['name'])[-12:].zfill(12)
        texto += converter.to_ascii(recibo['communication2'])[0:134].ljust(134)
        texto += '\r\n'
        if len(texto) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 '
                        'characters long:\n%s') % ('Individual opcional 58',
                                                   texto), True)
        return texto

    @api.model
    def _registro_obligatorio_domicilio_58(self, recibo):
        """
        Registro obligatorio domicilio 58 para no domiciliados.

        Formato:
         ZONA  DESCRIPCION                    POS     LONGITUD TIPO
                                              INICIAL          REGISTRO
         A: A1 Código de Registro: 56         1       2        Numérico
         A2    Código de Dato: 76             3       2        Numérico
         B: B1 Código del Cliente Ordenante   5       12       Alfanumérico
               (NIF 9POS Y SUF 3POS)
         B2    Código de Referencia           17      12       Alfanumérico
         C:    Domicilio del Deudor           29      40       Alfanumérico
         D: D1 Plaza del Domicilio del Deudor 69      35       Alfanumérico
         D2    Código Postal del Domicilio    104     5        Numérico
               del Deudor
         E: E1 Localidad del Ordenante al     109     38       Alfanumérico
               que se anticipó el Crédito
         E2    Código de la Provincia de      147     2        Numérico
               esta Localidad
         F: F1 Fecha de origen en que se      149     6        Numérico
               formalizó el Cto.(DDMMAA)
         F2    Libre                          155     8        Alfanumérico
        """
        converter = self.env['payment.converter.spain']
        alt_format = self.order.mode.csb58_alt_address_format

        #
        # Obtenemos la dirección (por defecto) del partner, a imagen
        # y semejanza de lo que hace info_partner
        # del objeto payment.line (account_payment/payment.py),
        # Pero si no encontramos ninguna dirección por defecto,
        # tomamos la primera del partner.
        #
        st = ''
        code_zip = ''
        city = ''
        if recibo['partner_id'].address:
            ads = None
            for item in recibo['partner_id'].address:
                if item.type == 'default':
                    ads = item
                    break
            if not ads and len(recibo['partner_id'].address) > 0:
                ads = recibo['partner_id'].address[0]

            st = ads.street and ads.street or ''
            partner_zip = self.env['res.partner.zip']
            if 'zip_id' in ads:
                obj_zip_city = ads.zip_id and partner_zip.browse(
                    ads.zip_id.id, self.context) or ''
                code_zip = obj_zip_city and obj_zip_city.name or ''
                city = obj_zip_city and obj_zip_city.city or ''
            else:
                code_zip = ads.zip and ads.zip or ''
                city = ads.city and ads.city or ''
            #
            # Comprobamos el código postal:
            #   "Cuando no se conozca el código
            #    completo, se cumplimentara, al menos, las dos primeras
            #    posiciones que identifican la provincia, dejando el resto de
            #    posiciones a cero."
            #
            if len(code_zip) < 2:
                code_zip = ads.state_id and ads.state_id.code or ''

        #
        # Obtenemos la localidad y código de provincia del ordenante
        #
        ord_city = ''
        ord_state_code = ''
        if self.order.mode.partner_id.address:
            ads = None
            for item in self.order.mode.partner_id.address:
                if item.type == 'default':
                    ads = item
                    break
            if not ads and len(self.order.mode.partner_id.address) > 0:
                ads = self.order.mode.partner_id.address[0]

            ord_city = ads.state_id and ads.state_id.name or ''
            ord_state_code = ads.state_id and ads.state_id.code or ''

        #
        # Calculamos la 'Fecha de origen en que se formalizo el crédito
        # anticipado' esto es, la fecha de creación del recibo.
        #
        if recibo.get('create_date'):
            date_ct = datetime.strptime(recibo['create_date'],
                                        '%Y-%m-%d %H:%M:%S')
        elif recibo.get('ml_date_created'):
            date_ct = datetime.strptime(recibo['ml_date_created'], '%Y-%m-%d')
        else:
            date_ct = datetime.today()

        #
        # Componemos la línea formateada
        #
        texto = '5676'
        texto += (self.order.mode.bank_id.partner_id.vat[2:] +
                  self.order.mode.csb_suffix).zfill(12)
        texto += str(recibo['name'])[-12:].zfill(12)
        texto += converter.to_ascii(st)[:40].ljust(40)       # Domicilio
        texto += converter.to_ascii(city)[:35].ljust(35)     # Plaza (ciudad)
        texto += converter.to_ascii(code_zip)[:5].zfill(5)   # CP
        # Localidad del ordenante (ciudad)
        texto += converter.to_ascii(ord_city)[:38].ljust(38)
        if alt_format:
            #
            # Si usamos el formato alternativo (basado en FacturaPlus)
            # escribimos la fecha en la posición 147 y dejamos dos carácteres
            # en blanco tras ella.
            # Lo correcto, según la norma, es que en la posición 147 aparezca
            # el código de provincia (2 dígitos) y la fecha empiece en
            # la posición 149.
            #
            texto += date_ct.strftime('%d%m%y')                 # Fecha crédito
            texto += 2*' '
        else:
            # Cod prov del ordenante
            texto += converter.to_ascii(ord_state_code)[:2].zfill(2)
            texto += date_ct.strftime('%d%m%y')                 # Fecha crédito
        texto += 8*' '                                  # Libre
        texto += '\r\n'
        if len(texto) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 '
                        'characters long:\n%s') % ('Obligatorio domicilio 58',
                                                   texto), True)
        return texto

    @api.model
    def _total_ordenante_58(self):
        texto = '5870'
        texto += (self.order.mode.bank_id.partner_id.vat[2:] +
                  self.order.mode.csb_suffix).zfill(12)
        texto += 72*' '
        totalordenante = int(round(abs(self.order.total) * 100, 0))
        texto += str(totalordenante).zfill(10)
        texto += 6*' '
        texto += str(self.num_recibos).zfill(10)
        texto += str(self.num_recibos + self.num_lines_opc + 2).zfill(10)
        texto += 38*' '
        texto += '\r\n'
        if len(texto) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 '
                        'characters long:\n%s') % ('Total ordenante 58',
                                                   texto), True)
        return texto

    @api.model
    def _total_general_58(self):
        texto = '5970'
        texto += (self.order.mode.bank_id.partner_id.vat[2:] +
                  self.order.mode.csb_suffix).zfill(12)
        texto += 52*' '
        texto += '0001'
        texto += 16*' '
        totalremesa = int(round(abs(self.order.total) * 100, 0))
        texto += str(totalremesa).zfill(10)
        texto += 6*' '
        texto += str(self.num_recibos).zfill(10)
        texto += str(self.num_recibos + self.num_lines_opc + 4).zfill(10)
        texto += 38*' '
        texto += '\r\n'
        if len(texto) != 164:
            raise Log(_('Configuration error:\n\nThe line "%s" is not 162 '
                        'characters long:\n%s') % ('Total general 58', texto),
                      True)
        return texto

    @api.model
    def create_file(self, order, lines):
        self.order = order

        txt_file = ''
        self.num_recibos = 0
        self.num_lines_opc = 0

        txt_file += self._cabecera_presentador_58()
        txt_file += self._cabecera_ordenante_58()

        for recibo in lines:
            txt_file += self._individual_obligatorio_58(recibo)
            self.num_recibos = self.num_recibos + 1

            # Sólo emitimos el registro individual si communication2 contiene
            # texto
            if (recibo['communication2'] and
                    len(recibo['communication2'].strip()) > 0):
                txt_file += self._individual_opcional_58(recibo)
                self.num_lines_opc = self.num_lines_opc + 1

            # Para recibos no domiciliados, añadimos el registro obligatorio
            # de domicilio (necesario con algunos bancos/cajas).
            if self.order.mode.csb58_include_address:
                txt_file += self._registro_obligatorio_domicilio_58(recibo)
                self.num_lines_opc = self.num_lines_opc + 1

        txt_file += self._total_ordenante_58()
        txt_file += self._total_general_58()

        return txt_file
