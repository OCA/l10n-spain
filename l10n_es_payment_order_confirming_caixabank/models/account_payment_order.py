# -*- coding: utf-8 -*-
# (c) 2018 Comunitea Servicios Tecnológicos - Javier Colmenero
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api, _
from odoo.exceptions import UserError
from datetime import date


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    @api.multi
    def generate_payment_file(self):
        self.ensure_one()
        if self.payment_method_id.code != 'conf_caixabank':
            return super(AccountPaymentOrder, self).generate_payment_file()
        self.num_records = 0
        txt_file = self._pop_cabecera()
        for line in self.bank_line_ids:
            txt_file += self._pop_beneficiarios(line)
        txt_file += self._pop_totales(line, self.num_records)
        return str.encode(txt_file), self.name + '.CAX'

    def _pop_cabecera(self):
        if self.date_prefered == 'due':
            fecha_planificada = self.payment_line_ids \
                and self.payment_line_ids[0].ml_maturity_date \
                or date.today().strftime('%Y-%d-%m')
            fecha_planificada = fecha_planificada.replace('-', '')
            dia = fecha_planificada[6:]
            mes = fecha_planificada[4:6]
            ano = fecha_planificada[:4]
            fecha_planificada = dia + mes + ano
        elif self.date_prefered == 'now':
            fecha_planificada = date.today().strftime('%d%m%Y')
        else:
            fecha_planificada = self.date_scheduled
            if not fecha_planificada:
                raise UserError(
                    _("Error: Fecha planificada no \
                        establecida en la Orden de pago."))
            else:
                fecha_planificada = fecha_planificada.replace('-', '')
                dia = fecha_planificada[6:]
                mes = fecha_planificada[4:6]
                ano = fecha_planificada[:4]
                fecha_planificada = dia + mes + ano

        all_text = ''
        for i in range(4):
            text = ''
            # 1 - 2: Código registro
            text += '01'

            # 3 - 4: Codigo operación
            text += '56'

            # 5 - 14: NIF ordenante
            vat = self.convert_vat(self.company_partner_bank_id.partner_id)
            text += self.convert(vat, 10)

            # 15 - 26: Libre
            text += 12 * ' '
            # 27 - 29: Numero del dato
            dato = '00'+str(i+1)
            text += dato
            if (i+1) == 1:  # Tipo registro 1, línea 1
                # 30 - 35: Fecha creación del fichero
                text += date.today().strftime('%d%m%y')
                # 36 - 41: Libre
                text += 6 * ' '

                cuenta = self.company_partner_bank_id.acc_number
                cuenta = cuenta.replace(' ', '')
                tipo_cuenta = self.company_partner_bank_id.acc_type
                if tipo_cuenta == 'iban':
                    cuenta = cuenta[4:]
                entidad = '2100' or cuenta[0:4]
                oficina = '6202' or cuenta[5:9]
                num_contrato = self.payment_mode_id.num_contract
                # 42 - 45: Entidad de destino del soporte
                text += entidad
                # 46 - 49: Oficina de destino del soporte
                text += oficina
                # 50 - 59: Número de contrato de confirming
                text += num_contrato

                # 60: Detalle del cargo
                text += '0'  # segun la documentacvión es 1??
                # 61 - 63: Moneda de soporte
                text += 'EUR'
                # 64 - 65: Libre
                text += 2 * ' '
                # 66 - 72: Libre
                text += 7 * ' '
            if (i+1) == 2:
                ordenante = self.company_partner_bank_id.partner_id.name
                if not ordenante:
                    raise UserError(
                        _("Error: Propietario de la cuenta no establecido para\
                        la cuenta %s.") %
                        self.company_partner_bank_id.acc_number)
                if len(ordenante) <= 36:
                    relleno = 36 - len(ordenante)
                    ordenante += relleno * ' '
                elif len(ordenante) > 36:
                    ordenante = ordenante[:36]
                text += ordenante.upper()
            if (i+1) == 3:
                domicilio_pro = self.company_partner_bank_id.partner_id.street
                if not domicilio_pro:
                    raise UserError(
                        _("Error: El Ordenante %s no tiene \
                        establecido el Domicilio.\
                         ") % self.company_partner_bank_id.partner_id.name)
                else:
                    if len(domicilio_pro) < 36:
                        relleno = 36 - len(domicilio_pro)
                        domicilio_pro += relleno * ' '
                    text += domicilio_pro.upper()
            if (i+1) == 4:
                ciudad_pro = self.company_partner_bank_id.partner_id.city
                if not ciudad_pro:
                    raise UserError(
                        _("Error: El Ordenante %s no tiene establecida la \
                        Ciudad.") %
                        self.company_partner_bank_id.partner_id.name)
                else:
                    if len(ciudad_pro) < 36:
                        relleno = 36 - len(ciudad_pro)
                        ciudad_pro += relleno * ' '
                    text += ciudad_pro.upper()

            text = text.ljust(100)+'\n'
            all_text += text
        return all_text

    def _pop_beneficiarios(self, line):
        all_text = ''
        bloque_registros = [
            '010', '043', '044', '011', '012', '014',
            '015', '016', '017', '018'
        ]
        fixed_text = ''
        # 1 - 2: Código registro
        fixed_text += '01'
        # 3 - 4: Codigo operación
        fixed_text += '56'
        # 5 - 14: NIF ordenante
        vat = self.convert_vat(self.company_partner_bank_id.partner_id)
        fixed_text += self.convert(vat, 10)
        # 15 - 26: Nif del proveedor o referencia interna
        nif = line['partner_id']['vat']
        if not nif:
            raise UserError(
                _("Error: El Proveedor %s no tiene establecido\
                 el NIF.") % line['partner_id']['name'])
        nif = self.convert_vat(self.company_partner_bank_id.partner_id)

        fixed_text += self.convert(vat, 12)

        for tipo_dato in bloque_registros:
            text = ''
            text += fixed_text
            # 27 - 29 Numero de dato
            text += tipo_dato

            ###################################################################
            if tipo_dato == '010':
                # 30 - 41 Importe
                amount_text = self.convert(abs(line['amount_currency']), 12)
                # Poner el signo negativo si procede
                if line.amount_currency > 0:
                    for i in range(0, len(amount_text)):
                        if i < len(amount_text) - 1 and \
                                amount_text[i] == '0' and \
                                amount_text[i + 1] != '0':
                            amount_text[i] == '-'
                text += amount_text
                # 42 - 59 Num banco, Num sucursal, Num cuenta
                control = ''
                if self.payment_mode_id.conf_caixabank_type == 'T':
                    cuenta = line['partner_bank_id']['acc_number']
                    cuenta = cuenta.replace(' ', '')
                    tipo_cuenta = self.company_partner_bank_id.acc_type
                    if tipo_cuenta == 'iban':
                        cuenta = cuenta[4:]
                    control = cuenta[8:10]
                    principio = cuenta[:8]
                    cuenta = principio + cuenta[10:]
                    text += cuenta
                else:
                    cuenta = 18 * ' '
                    text += cuenta

                # 60: Gastos por cuenta del ordenante
                text += '1'
                # 61: Conceptos de la ordeb
                text += '9'
                # 62 - 63: Libre
                text += 2 * ' '

                # 64 - 65: Digito control
                if self.payment_mode_id.conf_caixabank_type != 'C':
                    text += control
                else:
                    text += '  '
                # 66: Proveedor no residente
                text += 'S'  # TODO: Quizás sea N
                # 67: Indicador confirmación
                text += 'C'
                # 68 - 70: Moneda de factura
                text += 'EUR'
                # 71 -72: Libre
                text += 2 * ' '
            ###################################################################

            ###################################################################
            if tipo_dato == '043':
                # 30 - 63: Cuenta de pago para proveedores
                cuenta = line['partner_bank_id']['acc_number']
                cuenta = cuenta.replace(' ', '')
                text += cuenta
                # 64: Concepto de la ordern
                text += '7'
                # 65 - 72 Libre
                text += 8 * ' '
            ###################################################################

            ###################################################################
            if tipo_dato == '044':
                # 30: Clave de gastos
                text += '1'
                # 31 - 32: Código ISO pais destino
                # TODO comprobar que es iban
                text += line['partner_bank_id']['acc_number'][:2]
                # 63 - 38 Libre
                text += 6 * ' '
                # 39 - 50: Código SWIFT del banco destino (bic)
                # TODO Comprobar que hay banco y bic
                text += line['partner_bank_id']['bank_id']['bic']
                # 51 - 72 Libre
                text += 6 * ' '
            ###################################################################

            ###################################################################
            if tipo_dato == '011':
                # 30 - 65 Nombre del proveedor
                nombre_pro = line['partner_id']['name']
                if nombre_pro:
                    if len(nombre_pro) < 36:
                        relleno = 36 - len(nombre_pro)
                        nombre_pro += relleno * ' '
                    elif len(nombre_pro) > 36:
                        nombre_pro = nombre_pro[:36]
                    text += nombre_pro.upper()
                # 66 - 72 Libre
                text += 7 * ' '
            ###################################################################

            ###################################################################
            if tipo_dato == '012':
                # 30 - 65 Domicilio del proveedor
                domicilio_pro = line['partner_id']['street']
                if not domicilio_pro:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene\
                         establecido el Domicilio.\
                         ") % line['partner_id']['name'])
                else:
                    if len(domicilio_pro) < 36:
                        relleno = 36 - len(domicilio_pro)
                        domicilio_pro += relleno * ' '
                    text += domicilio_pro.upper()
                # 66 - 72 Libre
                text += 7 * ' '
            ###################################################################

            ###################################################################
            if tipo_dato == '014':
                # 30 - 34 CP
                cp_pro = line['partner_id']['zip']
                if not cp_pro:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene establecido\
                         el C.P.") % line['partner_id']['name'])
                else:
                    if len(cp_pro) < 5:
                        relleno = 5 - len(cp_pro)
                        cp_pro += relleno * ' '
                    text += cp_pro

                # 35 - 65 Plaza del proveedor
                ciudad_pro = line['partner_id']['city']
                if not ciudad_pro:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene establecida\
                         la Ciudad.") % line['partner_id']['name'])
                else:
                    if len(ciudad_pro) < 31:
                        relleno = 31 - len(ciudad_pro)
                        ciudad_pro += relleno * ' '
                    text += ciudad_pro
                # 66 - 72 Libre
                text += 7 * ' '
            ###################################################################

            ###################################################################
            if tipo_dato == '015':
                # 30 - 44: Código interno proveedor
                text += line.payment_line_ids[0].\
                    move_line_id.invoice_id.reference
                # 45 - 66: Nif de la factura si está endosada
                text += 12 * ' '  # TODO
                # 57 Clasificación proveedor
                text += ' '
                # 58 - 59: Código ISO país destino
                pais = line.partner_id.country_id
                if not pais:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene establecida\
                         el país.") % line['partner_id']['name'])
                text += pais.code.upper()
                # 60 - 68: País destino
                text += pais.name.upper()
                # 69 - 72 Libre
                text += 4 * ' '
            ###################################################################

            ###################################################################
            if tipo_dato == '016':
                # 30: Forma de pago
                if self.payment_mode_id.conf_caixabank_type == 'T':
                    text += 'T'
                else:
                    text = 'C'
                # 31 - 36: Fecha factura
                fecha_factura = 6 * ' '
                invoice = line.payment_line_ids[0].move_line_id.invoice_id
                if invoice:
                    fecha_factura = invoice.date_invoice.replace('-', '')
                    dia = fecha_factura[6:]
                    mes = fecha_factura[4:6]
                    ano = fecha_factura[2:4]
                    fecha_factura = dia + mes + ano
                text += fecha_factura
                # 37 - 51: Número factura
                num_factura = 15 * ' '
                if invoice:
                    num_factura = invoice.number.replace('-', '')
                    if len(num_factura) < 15:
                        relleno = 15 - len(num_factura)
                        num_factura += relleno * ' '
                    if len(num_factura) > 15:
                        num_factura = num_factura[-15:]
                    text += num_factura
                # 52 - 57: Fecha de vencimiento
                fecha_vencimiento = 6 * ' '
                if line.payment_line_ids.ml_maturity_date:
                    fecha_vencimiento = line.payment_line_ids.ml_maturity_date\
                        .replace('-', '')
                    dia = fecha_vencimiento[6:]
                    mes = fecha_vencimiento[4:6]
                    ano = fecha_vencimiento[2:4]
                    fecha_vencimiento = dia + mes + ano
                text += fecha_vencimiento

                # 58 - 65 Libre
                text += 8 * ' '
                # 66 - 72 Libre
                text += 7 * ' '
            ###################################################################

            ###################################################################
            if tipo_dato == '017':
                # 30 - 44 Referencia o número de la factura
                referencia_factura = 15 * ' '
                if invoice:
                    referencia_factura = invoice.reference.replace('-', '')
                    if len(referencia_factura) < 15:
                        relleno = 15 - len(referencia_factura)
                        referencia_factura += relleno * ' '
                    elif len(referencia_factura) > 15:
                        referencia_factura = referencia_factura[:15]
                text += referencia_factura
                # 45 - 59 Orden de pago, contenido libre
                orden_pago = self.name
                if len(orden_pago) < 15:
                    relleno = 15 - len(orden_pago)
                    orden_pago += relleno * ' '
                elif len(orden_pago) > 15:
                    orden_pago = orden_pago[:15]
                # 60 - 65 Libre
                text += 6 * ' '
                # 66 - 72 Libre
                text += 7 * ' '

            ###################################################################
            if tipo_dato == '018':
                # 30 - 44: Teléfono proveedor
                if line.partner_id.phone:  # TODO no coincide con el ejemplo
                    text += line.partner_id.phone
                # 60 - 65 FAX proveedor
                if line.partner_id.mobile:
                    text += line.partner_id.mobile[:5]  # TODO FAX, no hay?
                # 60 - 65 Libre
                text += 6 * ' '
                # 66 - 72 Libre
                text += 7 * ' '
            ###################################################################
            text = text.ljust(100)+'\n'
            all_text += text
        self.num_records += 1
        return all_text

    def _pop_totales(self, line, num_records):
            text = ''
            # 1 - 2: Código registro
            text += '01'
            # 3 - 4: Codigo operación
            text += '56'

            # 5 - 14: NIF ordenante
            vat = self.convert_vat(self.company_partner_bank_id.partner_id)
            text += self.convert(vat, 10)

            # 15 - 26: Libre
            text += 12 * ' '
            # 27 - 29: Numero del dato
            text += 3 * ' '

            # 30 - 41: Suma importes ajustado derecha completado con 0s
            text += self.convert(abs(self.total_amount), 12)
            # 42 - 49 Num de registros de dato 010
            num = str(num_records)
            text += num.zfill(8)
            # 50 - 59: Número total de registros del cuaderno (cab y totales)
            total_reg = num_records + 2
            total_reg = str(total_reg)
            text += total_reg.zfill(10)
            # 60 - 65 Libre
            text += 6 * ' '
            # 66 - 72 Libre
            text += 7 * ' '

            text = text.ljust(100)+'\n'
            return text
