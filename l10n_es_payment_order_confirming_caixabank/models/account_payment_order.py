# -*- coding: utf-8 -*-
# (c) 2018 Comunitea Servicios Tecnológicos - Javier Colmenero
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api, _, fields
from odoo.exceptions import UserError
from datetime import date


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def strim_txt(self, text, size):
        """
        Devuelvo el texto con espacios al final hasta completar size
        """
        if text:
            if len(text) < size:
                relleno = size - len(text)
                text += relleno * ' '
            elif len(text) > size:
                text = text[:size]
        return text

    @api.multi
    def generate_payment_file(self):
        self.ensure_one()
        if self.payment_method_id.code != 'conf_caixabank':
            return super(AccountPaymentOrder, self).generate_payment_file()
        self.num_lineas = 0
        txt_file = self._pop_cabecera_conf_caix()
        for line in self.bank_line_ids:
            txt_file += self._pop_beneficiarios_conf_caix(line)
        txt_file += self._pop_totales_conf_caix(line, self.num_lineas)
        # return str.encode(txt_file, 'ascii'), self.name + '.CAX'
        return self.to_ascii(txt_file).encode('ascii','ignore'), self.name + '.CAX'

    def _pop_cabecera_conf_caix(self):
        """
        Devuelve las 4 líneas de la cabecera
        """

        if self.date_prefered != 'fixed':
            fecha_planificada = self.date_scheduled
            fecha_planificada = fecha_planificada.replace('-', '')
            dia = fecha_planificada[6:]
            mes = fecha_planificada[4:6]
            ano = fecha_planificada[2:4]
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
            dato = '00' + str(i + 1)
            text += dato

            # LINEA 1
            ###################################################################
            if (i + 1) == 1:  # Tipo registro 1, línea 1
                # 30 - 35: Fecha creación del fichero
                text += date.today().strftime('%d%m%y')
                # 36 - 41: Libre
                text += 6 * ' '

                cuenta = self.company_partner_bank_id.acc_number
                cuenta = cuenta.replace(' ', '')
                tipo_cuenta = self.company_partner_bank_id.acc_type
                if tipo_cuenta == 'iban':
                    cuenta = cuenta[4:]
                entidad = '2100'
                oficina = '6202'
                # 42 - 45: Entidad de destino del soporte
                text += entidad
                # 46 - 49: Oficina de destino del soporte
                text += oficina
                # 50 - 59: Número de contrato de confirming
                num_contrato = self.payment_mode_id.num_contract
                if not num_contrato:
                    raise UserError(
                        _("Error: Falta el número de contrato en confirming"))
                text += num_contrato

                # 60: Detalle del cargo
                text += '0'  # segun la documentacvión es 1??
                # 61 - 63: Moneda de soporte
                text += 'EUR'
                # 64 - 65: Libre
                text += 2 * ' '
                # 66 - 72: Libre
                text += 7 * ' '
            ###################################################################

            # LINEA 2
            ###################################################################
            if (i + 1) == 2:
                ordenante = self.company_partner_bank_id.partner_id.name
                if not ordenante:
                    raise UserError(
                        _("Error: Propietario de la cuenta no establecido para\
                        la cuenta %s.") %
                        self.company_partner_bank_id.acc_number)
                ordenante = self.strim_txt(ordenante, 36)
                text += ordenante.upper()
            ###################################################################

            # LINEA 3
            ###################################################################
            if (i + 1) == 3:
                domicilio_pro = self.company_partner_bank_id.partner_id.street
                if not domicilio_pro:
                    raise UserError(
                        _("Error: El Ordenante %s no tiene \
                        establecido el Domicilio.\
                         ") % self.company_partner_bank_id.partner_id.name)
                domicilio_pro = self.strim_txt(domicilio_pro, 36)

                text += domicilio_pro.upper()
            ###################################################################

            # LINEA 4
            ###################################################################
            if (i + 1) == 4:
                ciudad_pro = self.company_partner_bank_id.partner_id.city
                if not ciudad_pro:
                    raise UserError(
                        _("Error: El Ordenante %s no tiene establecida la \
                        Ciudad.") %
                        self.company_partner_bank_id.partner_id.name)
                ciudad_pro = self.strim_txt(ciudad_pro, 36)
                text += ciudad_pro.upper()
            ###################################################################

            text += '\r\n'
            all_text += text
            self.num_lineas += 1
        return all_text

    def _get_signed_amount(self, amount_text):
        """
        Añade el signo al importe negativo
        """
        sign_text = ''
        for i in range(0, len(amount_text)):
            if i < (len(amount_text) - 1) and \
                    amount_text[i] == '0' and \
                    amount_text[i + 1] != '0':
                sign_text += '-'
                continue
            sign_text += amount_text[i]
        return sign_text

    def _pop_beneficiarios_conf_caix(self, line):
        all_text = ''
        bloque_registros = [
            '010', '043', '044', '046', '011', '012', '014',
            '015', '016', '017', '018', '019', '055'
        ]
        fixed_text = ''
        # 1 - 2: Código registro
        fixed_text += '06'
        # 3 - 4: Codigo operación
        fixed_text += '56'
        # 5 - 14: NIF ordenante
        vat = self.convert_vat(self.company_partner_bank_id.partner_id)
        fixed_text += self.convert(vat, 10)
        # 15 - 26: Nif del proveedor o referencia interna
        nif = line.partner_id.vat
        if not nif:
            raise UserError(
                _("Error: El Proveedor %s no tiene establecido\
                 el NIF.") % line.partner_id.name)
        nif = self.convert_vat(line.partner_id)

        fixed_text += self.convert(nif, 12)

        # Logica para saber si es nacional o no el banco
        country = line.partner_bank_id.acc_number and \
            line.partner_bank_id.acc_number[:2].upper() or ''
        is_national = country.upper() == 'ES' and True or False
        country_int_code = False
        if not is_national:
            country_int_code = self.env['res.country'].search([
                ('code', 'ilike', country)], limit=1).code

        for tipo_dato in bloque_registros:
            text = ''
            text += fixed_text
            # 27 - 29 Numero de dato
            text += tipo_dato
            # Supongo que en el confirming siempre hay una factura
            invoice = line.payment_line_ids[0].move_line_id.invoice_id

            # LÍNEA 1
            ###################################################################
            if tipo_dato == '010':
                # 30 - 41 Importe
                amount_text = self.convert(abs(line.amount_currency), 12)
                # Poner el signo negativo si procede
                if line.amount_currency < 0:
                    amount_text = self._get_signed_amount(amount_text)
                text += amount_text

                # 42 - 59 Num banco, Num sucursal, Num cuenta
                control = ''
                if self.payment_mode_id.conf_caixabank_type == 'T' and is_national:
                    cuenta = line.partner_bank_id.acc_number
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
                if self.payment_mode_id.conf_caixabank_type != 'C' and is_national:
                    text += control
                else:
                    text += '  '
                # 66: Proveedor no residente
                if not is_national and country_int_code:
                    text += 'S'
                else:
                    text += 'N'
                # 67: Indicador confirmación
                text += 'C'
                # 68 - 70: Moneda de factura
                text += 'EUR'
                # 71 -72: Libre
                text += 2 * ' '
            ###################################################################

            # LÍNEA 2
            ###################################################################
            if tipo_dato == '043':
                # 30 - 63: Cuenta de pago para proveedores
                cuenta = line.partner_bank_id.acc_number
                cuenta = cuenta.replace(' ', '')
                text +=  self.strim_txt(cuenta, 34)
                # 64: Concepto de la ordern
                text += '7'
                # 65 - 72 Libre
                text += 8 * ' '
            ###################################################################

            # LÍNEA 3
            ###################################################################
            if tipo_dato == '044':
                # 30: Clave de gastos
                text += '1'
                # 31 - 32: Código ISO pais destino
                if not is_national and country_int_code:
                    text += country_int_code
                else:
                    text += 'ES'
                # 63 - 38 Libre
                text += 6 * ' '
                # 39 - 50: Código SWIFT del banco destino (bic)
                if not line.partner_bank_id.bank_id:
                    raise UserError(
                        _("Error: No hay banco configurado para la cuenta \
                          %s") % line.partner_bank_id.acc_number)
                if not line.partner_bank_id.bank_id.bic:
                    raise UserError(
                        _("Error: No hay bic configurado para el banco \
                          %s") % line.partner_bank_id.name)

                text += line.partner_bank_id.bank_id.bic
                # 51 - 72 Libre
                text += 6 * ' '
            ###################################################################

            # LÍNEA 3bis
            ###################################################################
            if tipo_dato == '046':
                # 30 - 59 -- LARGO DE 30
                # Fecha de postfinanciación de la remesa.
                if not self.post_financing_date:
                    raise UserError(_('post-financing date mandatory'))
                # Asigno como fecha de vencimiento de la factura la fecha del ejecución del pago.
                text += fields.Date.from_string(self.post_financing_date).strftime('%d%m%y').ljust(30)

            ###################################################################


            # LÍNEA 4
            ###################################################################
            if tipo_dato == '011':
                # 30 - 65 Nombre del proveedor
                nombre_pro = self.strim_txt(line.partner_id.name, 36)
                text += nombre_pro.upper()
                # 66 - 72 Libre
                text += 7 * ' '
            ###################################################################

            # LÍNEA 5
            ###################################################################
            if tipo_dato == '012':
                # 30 - 65 Domicilio del proveedor
                if not line.partner_id.street:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene\
                         establecido el Domicilio.\
                         ") % line.partner_id.name)
                domicilio_pro = self.strim_txt(
                    line.partner_id.street, 36)
                text += domicilio_pro.upper()
                # 66 - 72 Libre
                text += 7 * ' '
            ###################################################################

            # LÍNEA 6
            ###################################################################
            if tipo_dato == '014':
                # 30 - 34 CP
                if not line.partner_id.zip:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene establecido\
                         el C.P.") % line.partner_id.name)
                cp_pro = self.strim_txt(line.partner_id.zip, 5)
                text += cp_pro.upper()

                # 35 - 65 Plaza del proveedor
                if not line.partner_id.city:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene establecida\
                         la Ciudad.") % line.partner_id.name)
                ciudad_pro = self.strim_txt(line.partner_id.city, 31)
                text += ciudad_pro.upper()
                # 66 - 72 Libre
                text += 7 * ' '
            ###################################################################

            # LÍNEA 7
            ###################################################################
            if tipo_dato == '015':
                # 30 - 44: Código interno proveedor
                if not line.partner_id.ref:
                    raise UserError(
                        _("Error: El proveedor %s no tiene establecido\
                          su código de referencia.") % line.partner_id.name)
                text += self.strim_txt(line.partner_id.ref, 15)
                # 45 - 66: Nif de la factura si está endosada, libre
                text += 12 * ' '
                # 57 Clasificación proveedor
                text += ' '
                # 58 - 59: Código ISO país destino
                pais = line.partner_id.country_id
                if not pais:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene establecida\
                         el país.") % line.partner_id.name)
                text += pais.code.upper()
                # 60 - 68: País destino
                text += self.strim_txt(pais.name.upper(), 9)
                # 69 - 72 Libre
                text += 4 * ' '
            ###################################################################

            # LÍNEA 8
            ###################################################################
            if tipo_dato == '016':
                # 30: Forma de pago
                text += 'T' if self.payment_mode_id.conf_caixabank_type == 'T'\
                    else 'C'
                # 31 - 36: Fecha factura
                fecha_factura = 6 * ' '
                if invoice.date_invoice:
                    fecha_factura = invoice.date_invoice.replace('-', '')
                    dia = fecha_factura[6:]
                    mes = fecha_factura[4:6]
                    ano = fecha_factura[2:4]
                    fecha_factura = dia + mes + ano
                else:
                    fecha_factura = fields.Date.from_string(line.payment_line_ids[0].move_line_id.date).strftime('%d%m%y')
                text += fecha_factura

                # 37 - 51: Número factura
                text += self.strim_txt(line.communication, 15)

                # 52 - 57: Fecha de vencimiento
                fecha_vencimiento = line.date.replace('-', '')
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

            # LÍNEA 9
            ###################################################################
            if tipo_dato == '017':
                # 30 - 44 Libre
                text += 15 * ' '

                # 45 - 59 Nif Proveedor para agrupar
                text += self.convert(nif, 15)

                # 60 - 65 Libre
                text += 6 * ' '
                # 66 - 72 Libre
                text += 7 * ' '
            ###################################################################

            # LÍNEA 10
            ###################################################################
            if tipo_dato == '018':
                # 30 - 44: Teléfono proveedor
                # TODO no coincide con el ejemplo si no existe el teléfono
                if line.partner_id.phone:
                    text += self.strim_txt(line.partner_id.phone, 15)
                else:
                    text += 15 * ' '

                # 60 - 65 FAX proveedor
                if line.partner_id.fax:
                    text += self.strim_txt(line.partner_id.fax, 15)
                else:
                    text += 15 * ' '
                # 60 - 65 Libre
                text += 6 * ' '
                # 66 - 72 Libre
                text += 7 * ' '
            ###################################################################

            # LÍNEA 11, opcional, solo si tiene mail
            ###################################################################
            if tipo_dato == '019' and line.partner_id.email:
                # 30 - 65 Email del proveedor
                email_pro = self.strim_txt(
                    line.partner_id.email, 36)
                text += email_pro
                # 66 - 72 Libre
                text += 7 * ' '
            ###################################################################

            # LÍNEA 16
            ###################################################################
            if tipo_dato == '055' and not is_national:
                # F1 30 - 31 Clase de Pago
                text += '01'
                # F2 32 - 37 Código estadístico CIN
                text += 6 * ' '
                # F3 38 - 39 Código ISO del Pais de destino del pago
                if country_int_code:
                    text += country_int_code
                else:
                    text += 2 * ' '
                # F4 40 - 48 NIF del Beneficiario
                text += 9 * ' '
                # F5 49 - 56 Número Operación Financiera
                text += 8 * ' '
                # F6 57 - 68 Código ISIN
                text += 12 * ' '
                # F7 69 - 72 Libre
                text += 4 * ' '
            ###################################################################
            text += '\r\n'
            all_text += text
            self.num_lineas += 1
        return all_text

    def _pop_totales_conf_caix(self, line, num_lineas):
            text = ''
            # 1 - 2: Código registro
            text += '08'
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
            text += self.convert(abs(self.total_company_currency), 12)
            # 42 - 49 Num de registros de dato 010
            num = str(self.bank_line_count)
            text += num.zfill(8)
            # 50 - 59: Número total de registros del cuaderno (cab y totales)
            total_reg = num_lineas + 1
            total_reg = str(total_reg)
            text += total_reg.zfill(10)
            # 60 - 65 Libre
            text += 6 * ' '
            # 66 - 72 Libre
            text += 7 * ' '

            text += '\r\n'
            return text
