# Copyright 2016 Soluntec Proyectos y Soluciones TIC. - Rubén Francés , Nacho Torró
# Copyright 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

from odoo import _, fields
from odoo.exceptions import UserError


class ConfirmingSabadell(object):
    def __init__(self, record):
        self.record = record

    def _sab_errors(self):
        # 4 - 43 Nombre ordenante
        if not self.record.company_partner_bank_id.partner_id:
            raise UserError(
                _("Propietario de la cuenta no establecido para la cuenta %s.")
                % self.record.company_partner_bank_id.acc_number
            )
        if not self.record.company_partner_bank_id.partner_id.vat:
            raise UserError(
                _("Propietario de la cuenta %s no tiene un NIF establecido.")
                % (self.record.company_partner_bank_id.display_name)
            )
        # Errores lineas
        for line in self.record.payment_line_ids:
            # 19 - 30 Documento identificativo
            if not line.partner_id.vat:
                raise UserError(
                    _("El Proveedor %s no tiene establecido el NIF.")
                    % line.partner_id.name
                )
            # 44 - 110 Domicilio
            if not line.partner_id.street:
                raise UserError(
                    _("El Proveedor %s no tiene establecido el Domicilio.")
                    % line.partner_id.name
                )
            # 52 - 66 Num Factura
            if line.move_line_id.ref and len(line.move_line_id.ref) > 15:
                raise UserError(
                    _(
                        "La referencia de factura %s de proveedor no puede ocupar "
                        "más de 15 caracteres."
                    )
                    % line.move_line_id.ref
                )
            # 111 - 150 Ciudad
            if not line.partner_id.city:
                raise UserError(
                    _("El Proveedor %s no tiene establecida la Ciudad.")
                    % line.partner_id.name
                )
            # 151- 155 CP
            if not line.partner_id.zip:
                raise UserError(
                    _("El Proveedor %s no tiene establecido el C.P.")
                    % line.partner_id.name
                )
            # 253 - 254 Codigo pais
            if not line.partner_id.country_id.code:
                raise UserError(
                    _("El Proveedor %s no tiene establecido el País.")
                    % line.partner_id.name
                )
            # 19 - 29 SWIFT
            if not line.partner_bank_id.bank_bic:
                raise UserError(
                    _(
                        "La cuenta bancaria del Proveedor %s no tiene establecido el SWIFT."
                    )
                    % line.partner_id.name
                )
            # 30 - 63 IBAN
            if (
                self.record.payment_mode_id.conf_sabadell_type == "58"
                and line.partner_bank_id.acc_type != "iban"
            ):
                raise UserError(
                    _("La Cuenta del Proveedor: %s tiene que estar en formato IBAN.")
                    % line.partner_id.name
                )

    def _sab_convert_text(self, text, size, justified="right"):
        text = text if text else ""
        if isinstance(text, float):
            text = str(int(round(text * 100, 0))).zfill(size)
        elif isinstance(text, int):
            text = str(text).zfill(size)
        else:
            if justified == "left":
                text = text[:size].ljust(size)
            else:
                text = text[:size].rjust(size)
        return text

    def _sab_tipo_vat(self, vat):
        if re.match(r"^ES[(0-9)]{8}$", vat):
            return "01"
        elif re.match(r"^ES[(0-9)]{8}[(a-zA-Z)]$", vat):
            return "02"
        elif re.match(r"^ESK[(0-9)]{7}[(a-zA-Z)]$", vat):
            return "02"
        elif re.match(r"^ESM[(0-9)]{7}[(a-zA-Z)]$", vat):
            return "02"
        elif re.match(r"^[(a-zA-Z)]{3}[(0-9)]{6}[(a-zA-Z0-9)]{0,1}$", vat):
            return "04"
        elif re.match(r"^ESX[(0-9)]{8}[(a-zA-Z)]{0,1}$", vat):
            return "05"
        elif re.match(r"^ESX[(0-9)]{7}[(a-zA-Z)]{0,1}$", vat):
            return "05"
        elif re.match(r"^ESY[(0-9)]{7}[(a-zA-Z)]{0,1}$", vat):
            return "05"
        elif re.match(r"^ESZ[(0-9)]{7}[(a-zA-Z)]{0,1}$", vat):
            return "05"
        elif re.match(
            r"^ES[abcdefghjpqrsuvABCDEFGHJPQRSUV]" "[(0-9)]{7}[(a-zA-Z0-9)]{0,2}$", vat
        ):
            return "10"
        elif re.match(r"^ES[anwNW][(0-9)]{7}[(a-zA-Z)]{0,2}$", vat):
            return "12"
        else:
            return "99"

    def create_file(self):
        # Sabadel payment file
        self._sab_errors()
        txt_file = self._sab_registro_01()
        for line in self.record.payment_line_ids:
            txt_file += self._sab_registro_02(line)
            txt_file += self._sab_registro_03(line)
            if self.record.payment_mode_id.conf_sabadell_type == "58":
                txt_file += self._sab_registro_04(line)
        txt_file += self._sab_registro_05()
        return txt_file.encode("utf-8"), "%s.txt" % self.record.name

    def _sab_registro_01(self):
        # Caracteres 1 y 2-3
        text = "1  "
        # 4 - 43 Nombre ordenante
        text += self._sab_convert_text(
            self.record.company_partner_bank_id.partner_id.name, 40, "left"
        )
        # 44 - 51 Fecha de proceso
        if self.record.date_prefered == "due":
            fecha_planificada = fields.first(
                self.record.payment_line_ids
            ).ml_maturity_date
        elif self.record.date_prefered == "now":
            fecha_planificada = fields.Date.today()
        else:
            fecha_planificada = self.record.date_scheduled
        text += str(fecha_planificada).replace("-", "")
        # 52 - 60 NIF
        vat = self.record.company_partner_bank_id.partner_id.vat
        if self.record.company_partner_bank_id.partner_id.country_id.code in vat:
            vat = vat.replace(
                self.record.company_partner_bank_id.partner_id.country_id.code, ""
            )
        text += self._sab_convert_text(vat, 9, "left")
        # 61 - 62 Tipo de Lote
        text += "65"
        # 63 - 64 Forma de envío
        text += "B"
        # 64 - 83 Cuenta de cargo
        cuenta = self.record.company_partner_bank_id.acc_number.replace(" ", "")
        if self.record.company_partner_bank_id.acc_type != "bank":
            cuenta = cuenta[4:]
        text += cuenta
        # 84 - 95 Contrato BSConfirming
        text += self.record.payment_mode_id.contrato_bsconfirming
        # 96 - 99 Codigo fichero
        text += "KF01"
        # 100 - 102 Codigo divisa
        text += self.record.company_currency_id.name
        text += "\r\n"
        return text

    def _sab_registro_02(self, line):
        # 1 Codigo registro
        text = "2"
        # 2 - 16 Codigo Proveedor
        text += self._sab_convert_text(line.partner_id.ref, 15, "left")
        # 17 - 18 Tipo de documento
        text += self._sab_tipo_vat(line.partner_id.vat)
        # 19 - 30 Documento identificativo
        vat = line.partner_id.vat
        if line.partner_id.country_id.code in vat:
            vat = vat.replace(line.partner_id.country_id.code, "")
        text += self._sab_convert_text(vat, 12, "left")
        # 31 Forma de pago
        forma_pago_value = {"56": "T", "57": "C", "58": "E"}
        forma_pago = forma_pago_value[self.record.payment_mode_id.conf_sabadell_type]
        text += forma_pago
        # 32 - 51 Cuenta
        cuenta = (
            line.partner_bank_id.acc_number.replace(" ", "")
            if forma_pago == "T" and line.partner_bank_id.acc_type == "bank"
            else ""
        )
        text += self._sab_convert_text(cuenta, 20, "left")
        # 52 - 66 Num Factura
        num_factura = (
            line.move_line_id.ref if line.move_line_id.ref else line.communication
        )
        text += self._sab_convert_text(num_factura, 15, "left")
        # 67 - 81 Importe de la factura
        text += self._sab_convert_text(line.amount_currency, 14)
        signo_factura = "+" if line.amount_currency >= 0 else "-"
        text += signo_factura
        # 82 - 89 Fecha factura
        fecha_factura = (
            str(line.move_line_id.date) if line.move_line_id.date else str(line.date)
        )
        text += self._sab_convert_text(
            fecha_factura.replace("-", "").replace("/", ""), 8, "left"
        )
        # 90 - 97 Fecha vencimiento
        # fecha_vencimiento = 8 * ' '
        text += str(line.date).replace("-", "").replace("/", "")
        # 98 - 127 Referencia factura ordenante
        referencia_factura = (
            str(line.move_line_id.move_id.name)
            if line.move_line_id.move_id.name
            else line.communication
        )
        text += self._sab_convert_text(referencia_factura.replace("-", ""), 30, "left")
        # 128 - Barrado cheque
        barrado_cheque = "S" if forma_pago == "C" else " "
        text += barrado_cheque
        # 129 - 136 fecha emision pagaré
        text += self._sab_convert_text("", 8, "left")
        # 137 -144 fecha vencimiento pagaré
        text += self._sab_convert_text("", 8, "left")
        # 145 tipo pagare
        text += " "
        # 146 - 175 IBAN
        iban = (
            line.partner_bank_id.acc_number.replace(" ", "")
            if forma_pago == "T" and line.partner_bank_id.acc_type == "iban"
            else ""
        )
        text += self._sab_convert_text(iban, 30, "left")
        # 176 Reservado
        text += self._sab_convert_text("", 125)
        text += "\r\n"
        return text

    def _sab_registro_03(self, line):
        # 1 Codigo registro
        text = "3"
        # 2 - 40 Nombre Proveedor
        text += self._sab_convert_text(line.partner_id.name, 40, "left")
        # 42 - 43 Idioma proveedor
        idioma_pro = line.partner_id.lang[:2].upper() if line.partner_id.lang else "3"
        text += self._sab_convert_text(idioma_pro, 2, "left")
        # 44 - 110 Domicilio
        text += self._sab_convert_text(line.partner_id.street, 67, "left")
        # 111 - 150 Ciudad
        text += self._sab_convert_text(line.partner_id.city, 40, "left")
        # 151- 155 CP
        text += self._sab_convert_text(line.partner_id.zip, 5, "left")
        # 156 - 161 Reservado no se utiliza
        text += self._sab_convert_text("", 6)
        # 162 - 176 Telefono
        telefono_pro = (
            line.partner_id.phone.replace(" ", "").replace("+", "")
            if line.partner_id.phone
            else ""
        )
        text += self._sab_convert_text(telefono_pro, 15, "left")
        # 177 - 191 fax
        text += self._sab_convert_text("", 15, "left")
        # 192 - 251 Correo
        text += self._sab_convert_text(line.partner_id.email, 60, "left")
        # 252 Tipo envio informacion
        # Por correo 1, por fax 2, por email 3
        text += self.record.payment_mode_id.tipo_envio_info
        # 253 - 254 Codigo pais
        text += line.partner_id.country_id.code
        # 255 -256 Codigo pais residencia no se usa
        text += "  "
        # 257 --- Reservado
        text += self._sab_convert_text("", 44)
        text += "\r\n"
        return text

    def _sab_registro_04(self, line):
        # 1 Codigo registro
        text = "4"
        # 2 -16 Codigo proveedor
        codigo_pro = line.partner_id.ref if line.partner_id.ref else ""
        text += self._sab_convert_text(codigo_pro, 15, "left")
        # 17 - 18 Codigo Pais
        text += line.partner_id.country_id.code
        # 19 - 29 SWIFT
        text += self._sab_convert_text(line.partner_bank_id.bank_bic, 11, "left")
        # 30 - 63 IBAN
        iban = (
            line.partner_bank_id.acc_number.replace(" ", "")
            if (
                self.record.payment_mode_id.conf_sabadell_type == "58"
                and line.partner_bank_id.acc_type == "iban"
            )
            else ""
        )
        text += self._sab_convert_text(iban, 34, "left")
        # 64 - 69 Codigo estadistico
        text += self.record.payment_mode_id.codigo_estadistico
        # 70 Divisa
        text += self.record.company_currency_id.name
        text += "\r\n"
        return text

    def _sab_registro_05(self):
        text = "5"
        # 2 - 10 NIF
        vat = self.record.company_partner_bank_id.partner_id.vat
        if self.record.company_partner_bank_id.partner_id.country_id.code in vat:
            vat = vat.replace(
                self.record.company_partner_bank_id.partner_id.country_id.code, ""
            )
        text += self._sab_convert_text(vat, 9, "left")
        # 11 - 17 Total ordenes
        text += self._sab_convert_text(len(self.record.payment_line_ids), 7)
        # 18 - 32  - Total importes
        total_amount = sum(self.record.payment_line_ids.mapped("amount_currency"))
        text += self._sab_convert_text(total_amount, 14)
        importe_sign = "+" if total_amount >= 0 else "-"
        text += importe_sign
        # 60-72 - Libre
        text += self._sab_convert_text("", 268)
        text += "\r\n"
        return text
