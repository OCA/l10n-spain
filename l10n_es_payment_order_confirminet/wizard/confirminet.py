# -*- coding: utf-8 -*-
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime
from openerp import fields, _
from openerp.addons.l10n_es_payment_order.wizard.log import Log
from openerp.addons.l10n_es_payment_order.wizard.converter import \
    PaymentConverterSpain


class Confirminet(object):
    def __init__(self, env):
        self.env = env
        self.converter = PaymentConverterSpain()

    def _start_registro_06(self, line):
        text = '06'
        # 3-4 - Forma de pago
        text += self.order.mode.confirminet_type
        # 5-14 - Código de ordenante
        vat = self.order.mode.bank_id.partner_id.vat[2:]
        text += self.converter.convert(vat, 10)
        # 15-26 - Referencia del proveedor
        if not line['partner_id'].vat:
            raise Log(_("Error: Supplier %s must have a VAT number.") %
                      line['partner_id'].name)
        partner_vat = line['partner_id'].vat[2:]
        text += self.converter.convert(partner_vat[-12:], 12)
        return text

    def _registro_03(self):
        today = datetime.today().strftime('%y%m%d')
        text = '0360'
        # 5-14 - NIF
        vat = self.order.mode.bank_id.partner_id.vat[2:]
        text += self.converter.convert(vat, 10)
        # 15-26 - Referencia interna BK - En blanco
        text += 12 * ' '
        # 27-29 - Número de dato
        text += '001'
        # 30-35 - Fecha de envío
        text += today
        # 36-41 - Fecha de emisión
        if self.order.date_scheduled:
            planned = fields.Date.from_string(self.order.date_scheduled)
            text += planned.strftime('%y%m%d')
        else:
            text += today
        # 42-65 - Contrato G.I.P.
        gip = self.converter.digits_only(self.order.mode.bank_id.acc_number)
        if gip[:4] != '0128':
            raise Log(
                _("Error: Contract number (Account number) is not valid. It "
                  "should start with '0128'."))
        text += gip[:4]
        text += gip[4:8]
        text += gip[10:20]
        text += 4 * " "
        text += gip[8:10]
        # 66-72 - Libre
        text += 7 * ' '
        text += '\r\n'
        self.num_records += 1
        return text

    def _registro_06_010(self, line):
        text = self._start_registro_06(line)
        text += '010'
        # 30-41 - Importe de la factura
        text += self.converter.convert(abs(line['amount']), 12)
        # 42-69 - Libre
        text += 19 * " "
        # 61-61 Signo del importe de la factura
        text += " " if line['amount'] >= 0 else "-"
        # 62-72 - Libre
        text += 11 * " "
        text += '\r\n'
        self.num_records += 1
        return text

    def _registro_06_011(self, line):
        text = self._start_registro_06(line)
        text += '011'
        # 30-65 - Nombre del proveedor
        text += self.converter.convert(line['partner_id'].name, 36)
        # 66-72 - Libre
        text += 7 * " "
        text += '\r\n'
        self.num_records += 1
        return text

    def _registro_06_012(self, line):
        address = line['partner_id']
        text = self._start_registro_06(line)
        text += '012'
        # 30-65 - Dirección del proveedor
        if not address.street:
            raise Log(
                _("Error: Supplier %s has no street in its address.") %
                line['partner_id'].name)
        text += self.converter.convert(address.street, 36)
        # 66-72 - Libre
        text += 7 * " "
        text += '\r\n'
        self.num_records += 1
        return text

    def _registro_06_014(self, line):
        address = line['partner_id']
        if not address.zip:
            if not address.country_id or address.country_id.code == 'ES':
                raise Log(
                    _("Error: Supplier %s has no ZIP in its address.") %
                    line['partner_id'].name)
            else:
                # No exportar este registro para extranjeros sin dirección
                return ""
        text = self._start_registro_06(line)
        text += '014'
        # 30-34 - Código postal
        text += self.converter.convert(address.zip, 5)
        # 35-66 - Localidad del proveedor
        if not address.city:
            raise Log(
                _("Error: Supplier %s has no city in its address.") %
                line['partner_id'].name)
        text += self.converter.convert(address.city, 32)
        # 67-72 - Libre
        text += 6 * " "
        text += '\r\n'
        self.num_records += 1
        return text

    def _registro_06_170(self, line):
        if not line['partner_id'].email:
            return ""
        text = self._start_registro_06(line)
        text += '170'
        # 30-65 - Email de proveedor
        text += self.converter.convert(line['partner_id'].email, 36)
        # 66-72 - Libre
        text += 7 * " "
        text += '\r\n'
        self.num_records += 1
        return text

    def _registro_06_171(self, line):
        if len(line['partner_id'].email or '') <= 36:
            return ""
        text = self._start_registro_06(line)
        text += '171'
        # 30-65 - Email de proveedor (continuación)
        text += self.converter.convert(line['partner_id'].email[36:], 36)
        # 66-72 - Libre
        text += 7 * " "
        text += '\r\n'
        self.num_records += 1
        return text

    def _registro_06_172(self, line):
        if len(line['partner_id'].email or '') <= 72:
            return ""
        text = self._start_registro_06(line)
        text += '172'
        # 30-65 - Email de proveedor (continuación)
        text += self.converter.convert(line['partner_id'].email[72:], 36)
        # 66-72 - Libre
        text += 7 * " "
        text += '\r\n'
        self.num_records += 1
        return text

    def _registro_06_173(self, line):
        address = line['partner_id']
        text = self._start_registro_06(line)
        text += '173'
        # 30-63 - Cuenta del proveedor
        if self.order.mode.confirminet_type == '57':
            # Cheque - No hace falta cuenta
            text += 34 * " "
        else:
            if address.country_id.code == 'ES':
                ccc = self.converter.digits_only(line['bank_id'].acc_number)
                text += self.converter.convert('ES' + ccc, 34)
            else:
                if line['bank_id'].state != 'iban':
                    raise Log(
                        _("Bank account of supplier %s, which is of outside "
                          "of Spain, should be IBAN.") %
                        line['partner_id'].name)
                iban = self.converter.digits_only(line['bank_id'].acc_number)
                text += self.converter.convert(iban, 34)
        # 64-64 - Libre
        text += " "
        # 65-66 - Código SWIFT del país del proveedor
        if address.country_id.code == 'ES':
            text += "ES"
        else:
            text += line['bank_id'][:2]
        # 67-72 - Libre
        text += 6 * " "
        text += '\r\n'
        self.num_records += 1
        return text

    def _registro_06_174(self, line):
        address = line['partner_id']
        text = self._start_registro_06(line)
        text += '174'
        # 30-40 - Dirección Swift
        if self.order.mode.confirminet_type == '57':
            text += 11 * " "
        else:
            if (address.country_id.code != 'ES' and not
                    line['bank_id'].bank_bic):
                raise Log(
                    _("Partner %s doesn't have a SWIFT/BIC code in its bank "
                      "account.") % line['partner_id'].name)
            text += self.converter.convert(line['bank_id'].bank_bic, 11)
        # 41-56 Claves adicionales (ABA/BLZ/FW/SC...)
        text += 16 * " "
        # 57-72 - Libre
        text += 16 * " "
        text += '\r\n'
        self.num_records += 1
        return text

    def _registro_06_175(self, line):
        address = line['partner_id']
        text = self._start_registro_06(line)
        text += '175'
        # 30-30 - Idioma
        text += "I" if address.country_id.code != 'ES' else "E"
        # 31-72 - Libre
        text += 42 * " "
        text += '\r\n'
        self.num_records += 1
        return text

    def _registro_06_182(self, line):
        text = self._start_registro_06(line)
        text += '182'
        # 30-41 - Referencia del Proveedor
        partner_vat = line['partner_id'].vat[2:]
        text += self.converter.convert(partner_vat[-12:], 12)
        # 42-72 - Libre
        text += 31 * " "
        text += '\r\n'
        self.num_records += 1
        return text

    def _registro_06_018(self, line):
        text = self._start_registro_06(line)
        text += '018'
        # 30-35 - Fecha de vencimiento de la factura
        if line['date']:
            date = fields.Date.from_string(line['date'])
        elif self.order.date_scheduled:
            date = fields.Date.from_string(self.order.date_scheduled)
        else:
            date = datetime.today()
        text += date.strftime('%y%m%d')
        # 36-51 - Número de la factura
        invoice_number = (
            line['ml_inv_ref'] and
            (line['ml_inv_ref'][0].supplier_invoice_number or
             line['ml_inv_ref'][0].reference) or line['communication'])
        if not invoice_number:
            raise Log(
                _("Error: Line with ID %s has no reference nor invoice "
                  "number.") % line['id'])
        text += self.converter.convert(invoice_number, 16)
        # 56-65 - Referencia interna del cliente (Libre)
        text += self.converter.convert(line['communication'], 14)
        # 66-72 - Libre
        text += 7 * " "
        text += '\r\n'
        self.num_records += 1
        return text

    def _registro_06_019(self, line):
        text = self._start_registro_06(line)
        text += '019'
        # 30-41 - Libre. Se deja como referencia interna del Cliente
        text += 12 * " "
        text += '\r\n'
        self.num_records += 1
        return text

    def _registro_08(self, total_amount, num_lines, num_records):
        text = '0860'
        # 5-14 - NIF
        vat = self.order.mode.bank_id.partner_id.vat[2:]
        text += self.converter.convert(vat, 10)
        # 15-29 - Libre
        text += 15 * " "
        # 30-41 - Suma de importes
        text += self.converter.convert(total_amount, 12)
        # 42-49 - Número de registros de dato 010
        text += self.converter.convert(num_lines, 8)
        # 50-59 - Número total de registros
        text += self.converter.convert(num_records, 10)
        # 60-72 - Libre
        text += 13 * " "
        return text

    def create_file(self, order, lines):
        self.order = order
        self.num_records = 0
        txt_file = self._registro_03()
        total_amount = 0
        for line in lines:
            txt_file += self._registro_06_010(line)
            txt_file += self._registro_06_011(line)
            txt_file += self._registro_06_012(line)
            txt_file += self._registro_06_014(line)
            txt_file += self._registro_06_170(line)
            txt_file += self._registro_06_171(line)
            txt_file += self._registro_06_172(line)
            txt_file += self._registro_06_173(line)
            txt_file += self._registro_06_174(line)
            txt_file += self._registro_06_175(line)
            txt_file += self._registro_06_182(line)
            txt_file += self._registro_06_018(line)
            txt_file += self._registro_06_019(line)
            total_amount += abs(line['amount'])
        txt_file += self._registro_08(
            total_amount, len(lines), self.num_records + 1)
        return txt_file
