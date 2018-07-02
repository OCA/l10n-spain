# -*- coding: utf-8 -*-
# (c) 2016 Soluntec Proyectos y Soluciones TIC. - Rubén Francés , Nacho Torró
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re
import datetime
from openerp import _
from openerp.addons.l10n_es_payment_order.wizard.log import Log
from openerp.addons.l10n_es_payment_order.wizard.converter import \
    PaymentConverterSpain


class ConfirmingSabadell(object):
    def __init__(self, env):
        self.env = env
        self.converter = PaymentConverterSpain()

    def create_file(self, order, lines):
        self.order = order
        total_amount = 0
        if self.order.mode.type.code == 'conf_sabadell':
            txt_file = self._sab_registro_01()
            for line in lines:
                txt_file += self._sab_registro_02(line)
                txt_file += self._sab_registro_03(line)
                if order.mode.conf_sabadell_type == '58':
                    txt_file += self._sab_registro_04(line)
                total_amount += abs(line['amount'])
            txt_file += self._sab_registro_05(total_amount, len(lines))

        return txt_file

    def _sab_registro_01(self):
        if self.order.date_prefered == 'due':
            fecha_planificada = datetime.date.today().strftime('%Y-%m-%d')
            fecha_planificada = fecha_planificada.replace('-', '')
        elif self.order.date_prefered == 'now':
            fecha_planificada = datetime.date.today().strftime('%Y%m%d')
        else:
            fecha_planificada = self.order.date_scheduled
            if not fecha_planificada:
                raise Log(
                    _("Error: Fecha planificada no establecida en \
                        la Orden de pago."))
            else:
                fecha_planificada = fecha_planificada.replace('-', '')

        # Caracteres 1 y 2-3
        text = '1  '

        # 4 - 43 Nombre ordenante
        ordenante = self.order.mode.bank_id.partner_id.name
        if not ordenante:
            raise Log(
                _("Error: Propietario de la cuenta no \
                    establecido para la cuenta\
                    %s.") % self.order.mode.bank_id.acc_number)
        if len(ordenante) <= 40:
            relleno = 40 - len(ordenante)
            ordenante += relleno * ' '
        elif len(ordenante) > 40:
            ordenante = ordenante[:40]
        text += ordenante

        # 44 - 51 Fecha de proceso
        text += fecha_planificada

        # 52 - 60 NIF Ordenante
        vat = self.order.mode.bank_id.partner_id.vat[2:]
        text += self.converter.convert(vat, 9)

        # 61 - 62 Tipo de Lote
        text += '65'

        # 63 - 64 Forma de envío
        text += 'B'

        # 64 - 83 Cuenta de cargo
        tipo_cuenta = self.order.mode.bank_id.state
        cuenta = self.order.mode.bank_id.acc_number
        cuenta = cuenta.replace(' ', '')
        if tipo_cuenta == 'bank':
            text += cuenta
        else:
            cuenta = cuenta[4:]
            text += cuenta

        # 84 - 95 Contrato BSConfirming
        text += self.order.mode.contrato_bsconfirming

        # 96 - 99 Codigo fichero
        text += 'KF01'

        # 100 - 102 Codigo divisa
        text += 'EUR'
        text += '\r\n'

        return text

    def _sab_registro_02(self, line):
        # 1 Codigo registro
        text = '2'
        # 2 - 16 Codigo Proveedor
        codigo_pro = line['partner_id']['ref']
        if codigo_pro:
            text += codigo_pro
        else:
            text += 15 * ' '
        # 17 - 18 Tipo de documento
        tipo_doc = line['partner_id']['vat_type']
        if tipo_doc == '1':
            tipo_doc = '02'
        elif tipo_doc == '2':
            tipo_doc = '12'
        elif tipo_doc == '3':
            tipo_doc = '04'
        elif tipo_doc == '4':
            tipo_doc = '06'
        elif tipo_doc == '5':
            tipo_doc = '03'
        elif tipo_doc == '6':
            tipo_doc = '99'
        text += tipo_doc
        # 19 - 30 Documento identificativo
        nif = line['partner_id']['vat']
        if not nif:
            raise Log(
                _("Error: El Proveedor %s no tiene \
                    establecido el NIF.") % line['partner_id']['name'])
        if len(nif) < 12:
            relleno = 12 - len(nif)
            nif += relleno * ' '
        text += nif
        # 31 Forma de pago
        forma_pago = self.order.mode.conf_sabadell_type
        if forma_pago == '56':
            forma_pago = 'T'
        elif forma_pago == '57':
            forma_pago = 'C'
        elif forma_pago == '58':
            forma_pago = 'E'
        text += forma_pago
        # 32 - 51 Cuenta
        if forma_pago == 'T':
            tipo_cuenta = line['bank_id']['state']
            if tipo_cuenta == 'bank':
                cuenta = line['bank_id']['acc_number']
                cuenta = cuenta.replace(' ', '')
                text += cuenta
            else:
                text += 20 * ' '
        else:
            text += 20 * ' '
        # 52 - 66 Num Factura
        num_factura = 15 * ' '
        if line['ml_inv_ref'][0]['reference']:
            num_factura = line['ml_inv_ref'][0]['reference']
            if num_factura:
                if len(num_factura) < 15:
                    relleno = 15 - len(num_factura)
                    num_factura += relleno * ' '
        text += num_factura
        # 67 - 81 Importe de la factura
        text += self.converter.convert(abs(line['amount']), 14)
        if line['amount'] >= 0:
            text += '+'
        else:
            text += '-'

        # 82 - 89 Fecha factura
        fecha_factura = 8 * ' '
        if line['ml_inv_ref'][0]['reference']:
            fecha_factura = line['ml_inv_ref'][0]['date_invoice']\
                .replace('-', '')
        text += fecha_factura
        # 90 - 97 Fecha vencimiento
        # fecha_vencimiento = 8 * ' '
        fecha_vencimiento = line['date'].replace('-', '')
        text += fecha_vencimiento
        # 98 - 127 Referencia factura ordenante
        referencia_factura = 30 * ' '
        if line['ml_inv_ref'][0]['reference']:
            referencia_factura = line['ml_inv_ref'][0]['number']\
                .replace('-', '')
            if len(referencia_factura) < 30:
                relleno = 30 - len(referencia_factura)
                referencia_factura += relleno * ' '
        text += referencia_factura
        # 128 - Barrado cheque
        if forma_pago == 'C':
            text += 'S'
        else:
            text += ' '
        # 129 - 136 fecha emision pagaré
        text += 8 * ' '
        # 137 -144 fecha vencimiento pagaré
        text += 8 * ' '
        # 145 tipo pagare
        text += ' '
        # 146 - 175 IBAN
        if forma_pago == 'T':
            tipo_cuenta = line['bank_id']['state']
            if tipo_cuenta == 'iban':
                cuenta = line['bank_id']['acc_number']
                cuenta = cuenta.replace(' ', '')
                if len(cuenta) < 30:
                    relleno = 30 - len(cuenta)
                    cuenta += relleno * ' '
            text += cuenta
        else:
            text += 30 * ' '
        # 176 Reservado
        text += 125 * ' '
        text += '\r\n'

        return text

    def _sab_registro_03(self, line):
        # 1 Codigo registro
        text = '3'
        # 2 - 40 Nombre Proveedor
        nombre_pro = line['partner_id']['name']
        if nombre_pro:
            if len(nombre_pro) < 40:
                relleno = 40 - len(nombre_pro)
                nombre_pro += relleno * ' '
            elif len(nombre_pro) > 40:
                nombre_pro = nombre_pro[:40]
            text += nombre_pro
        else:
            text += 40 * ' '
        # 42 - 43 Idioma proveedor
        idioma_pro = line['partner_id']['lang']
        if idioma_pro:
            if idioma_pro == 'es_ES':
                text += '08'
            else:
                text += '13'
        else:
            text += 2 * ' '
        # 44 - 110 Domicilio
        domicilio_pro = line['partner_id']['street']
        if not domicilio_pro:
            raise Log(
                _("Error: El Proveedor %s no tiene establecido el \
                    Domicilio.") % line['partner_id']['name'])
        else:
            if len(domicilio_pro) < 67:
                relleno = 67 - len(domicilio_pro)
                domicilio_pro += relleno * ' '
            text += domicilio_pro

        # 111 - 150 Ciudad
        ciudad_pro = line['partner_id']['city']
        if not ciudad_pro:
            raise Log(
                _("Error: El Proveedor %s no tiene establecida la \
                    Ciudad.") % line['partner_id']['name'])
        else:
            if len(ciudad_pro) < 40:
                relleno = 40 - len(ciudad_pro)
                ciudad_pro += relleno * ' '
            text += ciudad_pro
        # 151- 155 CP
        cp_pro = line['partner_id']['zip']
        if not cp_pro:
            raise Log(
                _("Error: El Proveedor %s no tiene establecido el \
                    C.P.") % line['partner_id']['name'])
        else:
            if len(cp_pro) < 5:
                relleno = 5 - len(cp_pro)
                cp_pro += relleno * ' '
            text += cp_pro
        # 156 - 161 Reservado no se utiliza
        text += 6 * ' '
        # 162 - 176 Telefono
        telefono_pro = line['partner_id']['phone']
        if telefono_pro:
            telefono_pro = telefono_pro.replace(' ', '')
            telefono_pro = telefono_pro.replace('+', '')
            if len(telefono_pro) < 15:
                relleno = 15 - len(telefono_pro)
                telefono_pro += relleno * ' '
            text += telefono_pro
        else:
            text += 15 * ' '
        # 177 - 191 fax
        fax_pro = line['partner_id']['fax']
        if fax_pro:
            fax_pro = fax_pro.replace(' ', '')
            fax_pro = fax_pro.replace('+', '')
            if len(fax_pro) < 15:
                relleno = 15 - len(fax_pro)
                fax_pro += relleno * ' '
            text += fax_pro
        else:
            text += 15 * ' '
        # 192 - 251 Correo
        email_pro = line['partner_id']['email']
        if email_pro:
            if re.match(r'^[(a-z0-9\_\-\.)]+@[(a-z0-9\_\-\.)]+\.[(a-z)]{2,15}\
                    $', email_pro.lower()):
                if len(email_pro) < 60:
                    relleno = 60 - len(email_pro)
                    email_pro += relleno * ' '
                text += email_pro
            else:
                text += 60 * ' '
        else:
            text += 60 * ' '
        # 252 Tipo envio informacion
        # Por correo 1, por fax 2, por email 3
        text += self.order.mode.tipo_envio_info
        # 253 - 254 Codigo pais
        pais_pro = line['partner_id']['country_id']['code']
        if not pais_pro:
            raise Log(
                _("Error: El Proveedor %s no tiene establecido el \
                    País.") % line['partner_id']['name'])
        else:
            text += pais_pro

        # 255 -256 Codigo pais residencia no se usa
        text += '  '
        # 257 --- Reservado
        text += 44 * ' '
        text += '\r\n'

        return text

    def _sab_registro_04(self, line):
        # 1 Codigo registro
        text = '4'
        # 2 -16 Codigo proveedor
        codigo_pro = line['partner_id']['ref']
        if codigo_pro:
            text += codigo_pro
        else:
            text += 15 * ' '
        # 17 - 18 Codigo Pais
        pais_pro = line['partner_id']['country_id']['code']
        if not pais_pro:
            raise Log(
                _("Error: El Proveedor %s no tiene establecido el \
                    País.") % line['partner_id']['name'])
        else:
            text += pais_pro
        # 19 - 29 SWIFT
        swift_pro = line['bank_id']['bank_bic']
        if not swift_pro:
            raise Log(
                _("Error: La cuenta bancaria del Proveedor %s no tiene \
                    establecido el SWIFT.") % line['partner_id']['name'])
        else:
            if len(swift_pro) < 11:
                relleno = 11 - len(swift_pro)
                swift_pro += relleno * ' '
            text += swift_pro
        # 30 - 63 IBAN
        if self.order.mode.conf_sabadell_type == '58':
            tipo_cuenta = line['bank_id']['state']
            if tipo_cuenta == 'iban':
                cuenta = line['bank_id']['acc_number']
                cuenta = cuenta.replace(' ', '')
                if len(cuenta) < 34:
                    relleno = 34 - len(cuenta)
                    cuenta += relleno * ' '
            else:
                raise Log(
                    _("Error: La Cuenta del Proveedor: %s tiene que \
                        estar en formato IBAN.") % line['partner_id']['name'])
        text += cuenta

        # 64 - 69 Codigo estadistico
        text += self.order.mode.codigo_estadistico
        # 70 Divisa
        text += 'EUR'
        text += '\r\n'

        return text

    def _sab_registro_05(self, total_amount, num_lines):
        text = '5'
        # 2 - 10 NIF
        vat = self.order.mode.bank_id.partner_id.vat[2:]
        text += self.converter.convert(vat, 9)
        # 11 - 17 Total ordenes
        text += self.converter.convert(num_lines, 7)
        # 18 - 32  - Total importes
        text += self.converter.convert(total_amount, 14)
        if total_amount >= 0:
            text += '+'
        else:
            text += '-'
        # 60-72 - Libre
        text += 268 * " "
        text += '\r\n'

        return text
