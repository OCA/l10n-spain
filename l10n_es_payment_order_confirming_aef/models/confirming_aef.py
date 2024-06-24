# Copyright 2023 Tecnativa - Ernesto García Medina
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import _, fields
from odoo.exceptions import UserError


class ConfirmingAEF(object):
    def __init__(self, record):
        self.record = record
        self.partner_bank = record.company_partner_bank_id.partner_id

    def _aef_errors(self):
        validation_errors = []
        # Nombre ordenante
        if not self.partner_bank:
            validation_errors.append(
                _("- Propietario de la cuenta no establecido para la cuenta %s.")
                % self.record.company_partner_bank_id.acc_number
            )
        if not self.partner_bank.country_id:
            validation_errors.append(
                _("- País del propietario no establecido %s.") % self.partner_bank.name
            )
        # Errores lineas
        for line in self.record.payment_line_ids:
            # Documento identificativo
            if not line.partner_id.vat:
                validation_errors.append(
                    _("- El proveedor %s no tiene establecido el NIF.")
                    % line.partner_id.name
                )
            # Domicilio
            if not line.partner_id.street:
                validation_errors.append(
                    _("- El proveedor %s no tiene establecido el domicilio.")
                    % line.partner_id.name
                )
            # Num Factura
            if len(line.move_line_id.move_id.ref or "") > 15:
                validation_errors.append(
                    _(
                        "- La referencia de factura %s de proveedor no puede ocupar "
                        "más de 15 caracteres."
                    )
                    % line.move_line_id.move_id.ref
                )
            # Ciudad
            if not line.partner_id.city:
                validation_errors.append(
                    _("- El proveedor %s no tiene establecida la ciudad.")
                    % line.partner_id.name
                )
            # Codigo pais
            if not line.partner_id.country_id.code:
                validation_errors.append(
                    _("- El proveedor %s no tiene establecido el país.")
                    % line.partner_id.name
                )
            # SWIFT
            if not line.partner_bank_id.bank_bic:
                validation_errors.append(
                    _(
                        "- La cuenta bancaria del Proveedor %s no tiene establecido el SWIFT."
                    )
                    % line.partner_id.name
                )
            error = _("Se han encontrado los siguientes errores:\n")
            if validation_errors:
                error += "\n".join(validation_errors)
                raise UserError(error)

    def _aef_convert_text(self, text, size, justified="right"):
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

    def create_file(self):
        # AEF payment file
        self._aef_errors()
        txt_file = self._aef_registro_01()
        txt_file += self._aef_registro_02()
        for line in self.record.payment_line_ids:
            txt_file += self._aef_registro_03(line)
            txt_file += self._aef_registro_04(line)
            txt_file += self._aef_registro_05(line)
            txt_file += self._aef_registro_06(line)
        txt_file += self._aef_registro_07()
        return txt_file.encode("Windows-1252"), "%s.txt" % self.record.name

    def _aef_registro_01(self):
        # 1 Valor fijo - ok
        text = "1"
        # 2 - 51 Nombre Ordenante - ok
        text += self._aef_convert_text(self.partner_bank.name, 50, "left")
        # 52 - 66 NIF Ordenante -ok
        vat = self.partner_bank.vat
        code = self.partner_bank.country_id.code
        if vat and code in vat:
            vat = vat.replace(self.partner_bank.country_id.code, "")
        text += self._aef_convert_text(vat, 15, "left")
        # 67 - 74 Fecha proceso
        fecha_proceso = fields.Date.today()
        text += self._aef_convert_text(str(fecha_proceso).replace("-", ""), 8)
        # 75 - 82 Fecha remesa
        if self.record.date_prefered == "due":
            fecha_planificada = fields.first(
                self.record.payment_line_ids
            ).ml_maturity_date
        elif self.record.date_prefered == "now":
            fecha_planificada = fields.Date.today()
        else:
            fecha_planificada = self.record.date_scheduled
        text += self._aef_convert_text(str(fecha_planificada).replace("-", ""), 8)
        # 83 - 102 Num contrato
        contract_cxb = self.record.payment_mode_id.aef_confirming_contract
        text += self._aef_convert_text(contract_cxb, 20, "left")
        # 103 - 136 Cuenta de cargo
        cuenta = self.record.company_partner_bank_id.acc_number.replace(" ", "")
        text += self._aef_convert_text(cuenta, 34, "left")
        # 137 - 139 Código divisa
        text += self._aef_convert_text(self.record.company_currency_id.name, 3)
        # 140 - 140 Estandar / Pronto Pago/ Otros
        text += self._aef_convert_text(
            self.record.payment_mode_id.aef_confirming_modality or "", 1
        )
        # 141 - 170 Referencia/Nombre fichero
        text += self._aef_convert_text("", 30)
        # 171 - 172 Tipo Formato
        text += "FU"
        # 173 - 250 Espacios
        text += self._aef_convert_text("", 77)
        text += "\r\n"
        return text

    def _aef_registro_02(self):
        # 1 Valor fijo
        text = "2"
        # 2 - 66 Domicilio ordenante
        text += self._aef_convert_text(self.partner_bank.street, 65, "left")
        # 67 - 106 Población ordenante
        text += self._aef_convert_text(self.partner_bank.city, 40, "left")
        # 107 - 116 CP ordenante
        text += self._aef_convert_text(self.partner_bank.zip, 10, "left")
        # 117 - 250 Espacios
        text += self._aef_convert_text("", 133)
        text += "\r\n"
        return text

    def _aef_registro_03(self, line):
        # 1 Valor fijo
        text = "3"
        # 2 - 71 Nombre proveedor
        text += self._aef_convert_text(line.partner_id.name, 70, "left")
        # 72 - 91 Num identificacion
        vat = line.partner_id.vat
        if line.partner_id.country_id.code in vat:
            vat = vat.replace(line.partner_id.country_id.code, "")
        text += self._aef_convert_text(vat, 20, "left")
        # 92 - 156 Domicilio proveedor
        text += self._aef_convert_text(line.partner_id.street, 65, "left")
        # 157 - 196 Población proveedor
        text += self._aef_convert_text(line.partner_id.city, 40, "left")
        # 197 - 206 CP proveedor
        text += self._aef_convert_text(line.partner_id.zip or "", 10, "left")
        # 207 - 208 País proveedor
        text += line.partner_id.country_id.code
        # 209 - 250 Espacios
        text += self._aef_convert_text("", 41)
        text += "\r\n"
        return text

    def _aef_registro_04(self, line):
        # 1 Valor fijo
        text = "4"
        # 2-51 Email
        text += self._aef_convert_text(line.partner_id.email, 50, "left")
        # 52 - 101 Email secundario
        text += self._aef_convert_text("", 50)
        # 102 - 116 Teléfono
        text += self._aef_convert_text("", 15)
        # 117 - 131 FAX
        text += self._aef_convert_text("", 15)
        # 132 - 250 Espacios
        text += self._aef_convert_text("", 118)
        text += "\r\n"
        return text

    def _aef_registro_05(self, line):
        # 1 Valor fijo
        text = "5"
        # 2 - 2 Forma de pago
        text += self.record.payment_mode_id.aef_confirming_type
        # 3 - 36 IBAN
        iban = (
            line.partner_bank_id.acc_number.replace(" ", "")
            if (
                self.record.payment_mode_id.aef_confirming_type == "T"
                and line.partner_bank_id.acc_type == "iban"
            )
            else ""
        )
        text += self._aef_convert_text(iban, 34, "left")
        # 37 - 47 BIC
        text += self._aef_convert_text(line.partner_bank_id.bank_bic, 11, "left")
        # 48 - 81 Cuenta pagos internacionales (sin IBAN)
        text += self._aef_convert_text("", 34)
        # 82 - 83 Código país banco
        text += line.partner_id.country_id.code
        # 84 - 94 Codigo ABA
        text += self._aef_convert_text("", 11)
        # 95 - 96 Tipo Proveedor
        text += self._aef_convert_text("", 2)
        # 97 - 136 Por cuenta de
        text += self._aef_convert_text("", 40)
        # 137 - 250 Espacios
        text += self._aef_convert_text("", 113)
        text += "\r\n"
        return text

    def _aef_registro_06(self, line):
        # 1 Valor fijo
        text = "6"
        # 2 - 21 Num factura
        referencia_factura = line.move_line_id.move_id.ref or line.communication
        text += self._aef_convert_text(referencia_factura.replace("-", ""), 20, "left")
        # 22 - 22 signo
        signo_factura = "+" if line.amount_currency >= 0 else "-"
        text += signo_factura
        # 23 - 37 Importe factura
        text += self._aef_convert_text(line.amount_currency, 15)
        # 38 - 45 Fecha emisión
        fecha_factura = (
            str(line.move_line_id.date) if line.move_line_id.date else str(line.date)
        )
        text += self._aef_convert_text(
            fecha_factura.replace("-", "").replace("/", ""), 8, "left"
        )
        # 46 - 53 Fecha vencimiento
        text += str(line.date).replace("-", "").replace("/", "")
        # 54 - 61 Fecha prórroga / aplazamiento / cargo
        text += self._aef_convert_text("", 8)
        # 62 - 77 Referencia de pago
        text += self._aef_convert_text("", 16)
        # 78 - 250 Espacios
        text += self._aef_convert_text("", 172)
        text += "\r\n"
        return text

    def _aef_registro_07(self):
        # 1 Valor fijo
        text = "7"
        # 2 - 13 Total ordenes
        text += self._aef_convert_text(len(self.record.payment_line_ids), 12)
        # 14 - 28 Total importe
        total_amount = sum(self.record.payment_line_ids.mapped("amount_currency"))
        text += self._aef_convert_text(total_amount, 15)
        # 29 - 250 Espacios
        text += self._aef_convert_text("", 221)
        text += "\r\n"
        return text
