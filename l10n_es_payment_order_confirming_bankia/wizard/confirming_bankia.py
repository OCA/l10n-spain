# -*- coding: utf-8 -*-
# (c) 2016 Soluntec Proyectos y Soluciones TIC. - Rubén Francés , Nacho Torró
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import datetime
from openerp import fields, _
from openerp.addons.l10n_es_payment_order.wizard.log import Log
from openerp.addons.l10n_es_payment_order.wizard.converter import \
    PaymentConverterSpain


class ConfirmingBankia(object):
    def __init__(self, env):
        self.env = env
        self.converter = PaymentConverterSpain()

    def create_file(self, order, lines):
        self.order = order
        txt_file = ''
        if self.order.mode.type.code == 'conf_bankia':
            txt_file = self._ban_cabecera()
            for line in lines:
                txt_file += self._ban_beneficiarios(line)
            txt_file += self._ban_cola(len(lines))

        return txt_file

    def _ban_cabecera(self):
        if self.order.date_prefered == 'due':
            fecha_tratamiento = self.order.line_ids \
                and self.order.line_ids[0].ml_maturity_date \
                or datetime.date.today().strftime('%Y-%d-%m')
            fecha_tratamiento = fecha_tratamiento.replace('-', '')
            dia = fecha_tratamiento[6:]
            mes = fecha_tratamiento[4:6]
            ano = fecha_tratamiento[:4]
            fecha_tratamiento = dia + mes + ano
        elif self.order.date_prefered == 'now':
            fecha_tratamiento = datetime.date.today().strftime('%d%m%Y')
        else:
            fecha_tratamiento = self.order.date_scheduled
            if not fecha_tratamiento:
                raise Log(
                    _("Error: Fecha planificada no \
                        establecida en la Orden de pago."))
            else:
                fecha_tratamiento = fecha_tratamiento.replace('-', '')
                dia = fecha_tratamiento[6:]
                mes = fecha_tratamiento[4:6]
                ano = fecha_tratamiento[:4]
                fecha_tratamiento = dia + mes + ano
        # 0 -3 Tipo de registro
        text = '021'
        # 4 - 11 Fecha de soporte
        text += datetime.date.today().strftime('%d%m%Y')
        # 12 - 19 Fecha tratamiento, Sin uso
        text += fecha_tratamiento
        # 20 - 28 NIF Ordenante
        ordenante = self.order.mode.bank_id.partner_id
        if not ordenante:
            raise Log(
                _("Error: Propietario de la cuenta no \
                    establecido para la cuenta %s.") % ordenante.acc_number)
        else:
            vat = ordenante.vat[2:]
            text += self.converter.convert(vat, 9)
            # 29 - 58 Nombre Ordenante
            ordenante = self.order.mode.bank_id.partner_id.name
            if len(ordenante) < 30:
                relleno = 30 - len(ordenante)
                ordenante += relleno * ' '
            elif len(ordenante) > 30:
                ordenante = ordenante[:30]
            text += ordenante
        # 59 - 77 Entidad, Oficina y Numero de cuenta del contrato
        cuenta = self.order.mode.bank_id.acc_number
        cuenta = cuenta.replace(' ', '')
        tipo_cuenta = self.order.mode.bank_id.state
        if tipo_cuenta == 'iban':
            cuenta = cuenta[4:]
        principio = cuenta[:8]
        cuenta = principio + cuenta[10:]
        text += cuenta

        text = text.ljust(325)+'\r\n'
        return text

    def _ban_beneficiarios(self, line):
        # 0 - 3 Tipo de registro
        text = '022'
        # 4 - 13 NIF Proveedor
        nif = line['partner_id']['vat']
        if not nif:
            raise Log(
                _("Error: El Proveedor %s no tiene \
                    establecido el NIF.") % line['partner_id']['name'])
        nif = nif[2:]
        text += nif
        # 14 - 15 Codigo centro Proveedor
        text += '000'
        # 16 - 55 Nombre Proveedor
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
        # 56 - 105 Apellido1 y Apellido2 Proveedor
        text += 50 * ' '
        # 106 - 135 Domicilio Proveedor
        domicilio_pro = line['partner_id']['street']
        if not domicilio_pro:
            raise Log(
                _("Error: El Proveedor %s no tiene \
                    establecido el Domicilio.") % line['partner_id']['name'])
        else:
            if len(domicilio_pro) < 30:
                relleno = 30 - len(domicilio_pro)
                domicilio_pro += relleno * ' '
            text += domicilio_pro
        # 136 - 140 C.P. Proveedor
        cp_pro = line['partner_id']['zip']
        if not cp_pro:
            raise Log(
                _("Error: El Proveedor %s no tiene \
                    establecido el C.P.") % line['partner_id']['name'])
        else:
            if len(cp_pro) < 5:
                relleno = 5 - len(cp_pro)
                cp_pro += relleno * ' '
            text += cp_pro
        # 141 - 170 Ciudad Proveedor
        ciudad_pro = line['partner_id']['city']
        if not ciudad_pro:
            raise Log(
                _("Error: El Proveedor %s no tiene \
                    establecida la Ciudad.") % line['partner_id']['name'])
        else:
            if len(ciudad_pro) < 30:
                relleno = 30 - len(ciudad_pro)
                ciudad_pro += relleno * ' '
            text += ciudad_pro
        # 171 - 210 Email Proveedor, no obligatorio
        text += 40 * ' '
        # 211 - 219 Telefono, no obligatorio
        text += '000000000'
        # 220 - 228 Fax, no obligatorio
        text += '000000000'
        # 229 - 248 Cuenta Proveedor
        cuenta = line['bank_id']['acc_number']
        cuenta = cuenta.replace(' ', '')
        tipo_cuenta = self.order.mode.bank_id.state
        if tipo_cuenta == 'iban':
            cuenta = cuenta[4:]
        text += cuenta
        # 249 - 258 Numero Factura
        num_factura = 10 * ' '
        if line['ml_inv_ref'][0]['reference']:
            num_factura = line['ml_inv_ref'][0]['reference']
            if num_factura:
                if len(num_factura) < 10:
                    relleno = 10 - len(num_factura)
                    num_factura += relleno * ' '
            else:
                num_factura
        text += num_factura
        # 259 - 266 Fecha Factura
        fecha_factura = '00000000'
        if line['ml_inv_ref'][0]['reference']:
            fecha_factura = line['ml_inv_ref'][0]['date_invoice']\
                .replace('-', '')
            dia = fecha_factura[6:]
            mes = fecha_factura[4:6]
            ano = fecha_factura[:4]
            fecha_factura = dia + mes + ano
        text += fecha_factura
        # 267 - 281 Importe Factura
        text += self.converter.convert(abs(line['amount']), 15)
        # 282 Signo
        if line['amount'] >= 0:
            text += '+'
        else:
            text += '-'
        # 283 - 290 Fecha vencimiento
        fecha_vencimiento = '00000000'
        if line['ml_inv_ref'][0]['reference']:
            fecha_vencimiento = line['date'].replace('-', '')
            dia = fecha_vencimiento[6:]
            mes = fecha_vencimiento[4:6]
            ano = fecha_vencimiento[:4]
            fecha_vencimiento = dia + mes + ano
        text += fecha_vencimiento
        # 291 Medio de pago
        text += self.order.mode.conf_bankia_type
        # 292 - Fecha emision pago domicilado
        fecha_vencimiento = '00000000'
        if self.order.mode.conf_bankia_type == 'P':
            if line['ml_inv_ref'][0]['reference']:
                fecha_vencimiento = line['ml_inv_ref'][0]['date_due']\
                    .replace('-', '')
                dia = fecha_vencimiento[6:]
                mes = fecha_vencimiento[4:6]
                ano = fecha_vencimiento[:4]
                fecha_vencimiento = dia + mes + ano
        text += fecha_vencimiento
        text = text.ljust(325)+'\r\n'

        return text

    def _ban_cola(self, lines):
        # 0 - 3 Tipo de registro
        text = '023'
        # 4 - 8 Num total de facturas de la remesa
        numero_facturas = str(lines)
        text += numero_facturas.zfill(5)
        # 9 - 24
        text += self.converter.convert(self.order.total, 15)

        text = text.ljust(325)+'\r\n'

        return text
        