# -*- coding: utf-8 -*-
# (c) 2016 Soluntec Soluciones Tecnológicas. - Rubén Francés, Nacho Torró
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re
from datetime import datetime
from openerp import fields, _
from openerp.addons.l10n_es_payment_order.wizard.log import Log
from openerp.addons.l10n_es_payment_order.wizard.converter import \
    PaymentConverterSpain


class ConfirmingPopular(object):
    def __init__(self, env):
        self.env = env
        self.converter = PaymentConverterSpain()


    def create_file(self, order, lines):
        self.order = order
        self.num_records = 0
        total_amount = 0
        if self.order.mode.type.code == 'conf_popular':
            txt_file = self._pop_cabecera()
            for line in lines:
                txt_file += self._pop_beneficiarios(line)
                txt_file += self._pop_detalle(line)
            txt_file += self._pop_totales(line, self.num_records)
               
        return txt_file

    def _pop_cabecera(self):
        if self.order.date_prefered == 'now' or self.order.date_prefered == 'due':
            fecha_planificada = datetime.today().strftime('%d%m%Y')
        else:
            fecha_planificada = self.order.date_scheduled
            if not fecha_planificada:
                raise Log(
                    _("Error: Fecha planificada no establecida en la Orden de pago."))
            else:
                fecha_planificada = fecha_planificada.replace('-','')
                dia = fecha_planificada[6:]
                mes = fecha_planificada[4:6]
                ano = fecha_planificada[:4]
                fecha_planificada = dia + mes + ano
        text = ''
        for i in range(4):
            # 1 y 2
            text += '13'
            # 3 -4 Codigo operacion
            if self.order.mode.conf_popular_type == '70':
                text += '70'
            else:
                text += '60'
            # 5 - 14 Codigo ordenante
            text += '0'
            vat = self.order.mode.bank_id.partner_id.vat[2:]
            text += self.converter.convert(vat, 9)
            # 15 - 17 Sufijo
            text += '001'
            # 18 -26 Libre
            text += 9 * ' '
            # 27 Numero del dato
            dato = '00'+str(i+1)
            text += dato
            if (i+1) == 1:
                text += fecha_planificada
                text += fecha_planificada
                cuenta = self.order.mode.bank_id.acc_number
                cuenta = cuenta.replace(' ','')
                tipo_cuenta = self.order.mode.bank_id.state
                if tipo_cuenta == 'iban':
                    cuenta = cuenta[4:]
                control = cuenta[8:10]
                principio = cuenta[:8]
                cuenta = principio + cuenta[10:]
                text += cuenta
                if self.order.mode.conf_popular_type == '70':
                    text += ' 01 '
                else:
                    text += '0   '
                text += control
                text += 3 * ' '
            if (i+1) == 2:
                ordenante = self.order.mode.bank_id.partner_id.name
                if not ordenante:
                    raise Log(
                        _("Error: Propietario de la cuenta no establecido para la cuenta %s.") % self.order.mode.bank_id.acc_number)
                if len(ordenante) <= 36:
                    relleno = 36 - len(ordenante)
                    ordenante += relleno * ' '
                elif len(ordenante) > 36:
                    ordenante = ordenante[:36]
                text += ordenante
            if (i+1) == 3:
                domicilio_pro = self.order.mode.bank_id.partner_id.street
                if not domicilio_pro:
                    raise Log(
                        _("Error: El Ordenante %s no tiene establecido el Domicilio.") % self.order.mode.bank_id.partner_id.name)
                else:
                    if len(domicilio_pro) < 36:
                        relleno = 36 - len(domicilio_pro)
                        domicilio_pro += relleno * ' '
                    text += domicilio_pro
            if (i+1) == 4:
                ciudad_pro = self.order.mode.bank_id.partner_id.city
                if not ciudad_pro:
                    raise Log(
                        _("Error: El Ordenante %s no tiene establecida la Ciudad.") % self.order.mode.bank_id.partner_id.name)
                else:
                    if len(ciudad_pro) < 36:
                        relleno = 36 - len(ciudad_pro)
                        ciudad_pro += relleno * ' '
                    text += ciudad_pro

            text += '\r\n'
        return text

    def _pop_beneficiarios(self,line):
        text = ''
        for i in range(4):
            # 1 y 2
            text += '16'
            # 3 -4 Codigo operacion
            if self.order.mode.conf_popular_type == '70':
                text += '70'
            elif self.order.mode.conf_popular_type == '60':
                text += '60'
            elif self.order.mode.conf_popular_type == '61':
                text += '61'
            # 5 - 14 Codigo ordenante
            text += '0'
            vat = self.order.mode.bank_id.partner_id.vat[2:]
            text += self.converter.convert(vat, 9)
            # 15 - 26 NIF Beneficiario
            nif = line['partner_id']['vat']
            if not nif:
                raise Log(
                    _("Error: El Proveedor %s no tiene establecido el NIF.") % line['partner_id']['name'])
            nif = nif[2:]
            if len(nif) < 12:
                relleno = 12 - len(nif)
                nif = (relleno * '0') + nif
            text += nif
            if (i+1) == 1:
                # 27 - 29 Numero de dato
                text += '010'
                # 30 - 41 Importe
                text += self.converter.convert(abs(line['amount']), 12)
                # 42 - 59 Num banco, Num sucursal, Num cuenta
                if self.order.mode.conf_popular_type != '61':
                    cuenta = line['bank_id']['acc_number']
                    cuenta = cuenta.replace(' ','')
                    tipo_cuenta = self.order.mode.bank_id.state
                    if tipo_cuenta == 'iban':
                        cuenta = cuenta[4:]
                    control = cuenta[8:10]
                    principio = cuenta[:8]
                    cuenta = principio + cuenta[10:]
                    text += cuenta
                else:
                    cuenta = 18 * ' '
                    text += cuenta
                # 60 - 61 - 62  Gastos, Forma de pago, Libre
                if self.order.mode.conf_popular_type in ['60','61']:
                    if self.order.mode.gastos == 'ordenante':
                        text += '1  '
                    elif self.order.mode.gastos == 'beneficiario':
                        text += '2  '
                    else:
                        text += '   '
                elif self.order.mode.conf_popular_type == '70':
                    if self.order.mode.forma_pago == 'C':
                        text += ' C '
                    elif self.order.mode.forma_pago == 'T':
                        text += ' T '
                    else:
                        text += '   '
                # 63 - Digito control
                if self.order.mode.conf_popular_type != '61':
                    text += control
                else:
                    text += '  '
                # 65 - 72 Libre
                text += 8 * ' '
            if (i+1) == 2:
                # 27 - 29 Numero de dato
                text += '011'
                # 30 - 65 Nombre del beneficiario
                nombre_pro = line['partner_id']['name']
                if nombre_pro:
                    if len(nombre_pro) < 36:
                        relleno = 36 - len(nombre_pro)
                        nombre_pro += relleno * ' '
                    elif len(nombre_pro) > 36:
                        nombre_pro = nombre_pro[:36]
                    text += nombre_pro
                else:
                    text += 36 * ' '
                # 66 - 72 Libre
                text += 7 * ' '
            if (i+1) == 3:
                # 27 - 29 Numero de dato
                text += '012'
                # 30 - 65 Domicilio del beneficiario
                domicilio_pro = line['partner_id']['street']
                if not domicilio_pro:
                    raise Log(
                        _("Error: El Proveedor %s no tiene establecido el Domicilio.") % line['partner_id']['name'])
                else:
                    if len(domicilio_pro) < 36:
                        relleno = 36 - len(domicilio_pro)
                        domicilio_pro += relleno * ' '
                    text += domicilio_pro
                ## 66 - 72 Libre
                text += 7 * ' '
            if (i+1) == 4:
                # 27 - 29 Numero de dato
                text += '014'
                # 30 - 65 CP, Ciudad
                cp_pro = line['partner_id']['zip']
                if not cp_pro:
                    raise Log(
                        _("Error: El Proveedor %s no tiene establecido el C.P.") % line['partner_id']['name'])
                else:
                    if len(cp_pro) < 5:
                        relleno = 5 - len(cp_pro)
                        cp_pro += relleno * ' '
                    text += cp_pro
                ciudad_pro = line['partner_id']['city']
                if not ciudad_pro:
                    raise Log(
                        _("Error: El Proveedor %s no tiene establecida la Ciudad.") % line['partner_id']['name'])
                else:
                    if len(ciudad_pro) < 31:
                        relleno = 31 - len(ciudad_pro)
                        ciudad_pro += relleno * ' '
                    text += ciudad_pro
                ## 66 - 72 Libre
                text += 7 * ' '
            text += '\r\n'
        self.num_records += 1
        return text

    def _pop_detalle(self,line):
        text = ''
        # 1 y 2
        text += '17'
        # 3 -4 Codigo operacion
        if self.order.mode.conf_popular_type == '70':
            text += '70'
        elif self.order.mode.conf_popular_type == '60':
            text += '60'
        elif self.order.mode.conf_popular_type == '61':
            text += '61'
        # 5 - 14 Codigo ordenante
        text += '0'
        vat = self.order.mode.bank_id.partner_id.vat[2:]
        text += self.converter.convert(vat, 9)
        # 15 - 26 NIF Beneficiario
        nif = line['partner_id']['vat']
        if not nif:
            raise Log(
                _("Error: El Proveedor %s no tiene establecido el NIF.") % line['partner_id']['name'])
        nif = nif[2:]
        if len(nif) < 12:
            relleno = 12 - len(nif)
            nif = (relleno * '0') + nif
        text += nif
        # 27 - 29 Numero de dato
        text += '100'
        # 30 - 37 Fecha emisión Factura
        fecha_factura = 8 * ' '
        if line['ml_inv_ref'] > 0:
            fecha_factura = line['ml_inv_ref'][0]['date_invoice'].replace('-','')
            dia = fecha_factura[6:]
            mes = fecha_factura[4:6]
            ano = fecha_factura[:4]
            fecha_factura = dia + mes + ano
        text += fecha_factura
        # 38 - 45 Fecha vencimiento / Referencia factura
        if self.order.mode.conf_popular_type == '70':
            fecha_vencimiento = 8 * ' '
            if line['ml_inv_ref'] > 0:
                fecha_vencimiento = line['ml_inv_ref'][0]['date_due'].replace('-','')
                dia = fecha_vencimiento[6:]
                mes = fecha_vencimiento[4:6]
                ano = fecha_vencimiento[:4]
                fecha_vencimiento = dia + mes + ano
            text += fecha_vencimiento
        elif self.order.mode.conf_popular_type in ['60','61']:
            referencia_factura = 8 * ' '
            if line['ml_inv_ref'] > 0:
                referencia_factura = line['ml_inv_ref'][0]['reference'].replace('-','')
                if len(referencia_factura) < 8:
                    relleno = 8 - len(referencia_factura)
                    referencia_factura += relleno * ' '
                elif len(referencia_factura) > 8:
                    referencia_factura = referencia_factura[:8]
            text += referencia_factura
        # 46 - 59 Numero de factura
        num_factura = 14 * ' '
        if line['ml_inv_ref'] > 0:
            num_factura = line['ml_inv_ref'][0]['number'].replace('-','')
            if len(num_factura) < 8:
                relleno = 8 - len(num_factura)
                num_factura += relleno * ' '
            if len(num_factura) > 14:
                num_factura = num_factura[:14]
        text += num_factura
        # 60 - 71 Importe
        text += self.converter.convert(abs(line['amount']), 12)
        if line['amount'] >= 0:
            text += ' '
        else:
            text += '-'
        text += '\r\n'

        return text

    def _pop_totales(self,line,num_records):
        text = ''
        # 1 y 2
        text += '18'
        # 3 -4 Codigo operacion
        if self.order.mode.conf_popular_type == '70':
            text += '70'
        elif self.order.mode.conf_popular_type == '60':
            text += '60'
        elif self.order.mode.conf_popular_type == '61':
            text += '61'
        # 5 - 14 Codigo ordenante
        text += '0'
        vat = self.order.mode.bank_id.partner_id.vat[2:]
        text += self.converter.convert(vat, 9)
        # 15 - 29 Libre
        text += 15 * ' '
        # 30 - 41 Suma de importes
        text += self.converter.convert(abs(self.order.total), 12)
        # 42 - 49 Num de registros de dato 010
        num = str(num_records)
        text += num.zfill(8)

        # 50 - 59 Num total de registros
        total_reg = 4 + (num_records * 5) + 1
        total_reg = str(total_reg)
        text += total_reg.zfill(10)

        # 60 - 73 Libre
        text += 13 * ' '
        return text