# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, _, fields
from odoo.exceptions import UserError
import time
import datetime


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    def strim_txt(self, text, size, separator=' '):
        """
        Devuelvo el texto con espacios al final hasta completar size
        """
        if text:
            if len(text) < size:
                relleno = size - len(text)
                text += relleno * separator
            elif len(text) > size:
                text = text[:size]
        return text

    @api.model
    def ensure_valid_ascii(self, text):
        res = text.upper()
        to_replace = {
            'Á': 'A',
            'É': 'E',
            'Í': 'I',
            'Ó': 'O',
            'Ú': 'U',
        }
        for letter in to_replace:
            res.replace(letter, to_replace[letter])
        return res

    @api.multi
    def generate_payment_file(self):
        self.ensure_one()
        if self.payment_method_id.code != 'conf_sabadell':
            return super(AccountPaymentOrder, self).generate_payment_file()
        if self.date_prefered != 'fixed':
            raise UserError(_('Solo fecha fija'))
        # ##################################################
        # ##################################################
        # Importe total de la remesa
        self.importe_remesa = 0
        # ##################################################
        # ##################################################
        self.num_records = 0

        txt_file = self._pop_cabecera_sabadell()
        grouped_lines = self._group_by_partner(self.bank_line_ids)
        for partner in grouped_lines:
            lines = grouped_lines[partner]
            for line in lines:
                txt_file += self._pop_detalle_sabadell(line)
        txt_file += self._pop_totales_sabadell()
        # txt_file = self.ensure_valid_ascii(txt_file)

        return str.encode(txt_file, encoding='cp1252', errors='replace'), self.name + '.TXT'

    def _get_fix_part_sabadell(self, cr):
        # OJO sólo se cuentan los registros de tipo 2.
        if cr == "3":
            self.num_records += 1
        text = ''
        # A1. 1 a 2 código del registro
        text += cr

        return text

    def _pop_cabecera_sabadell(self):

        all_text = ''
        text = self._get_fix_part_sabadell('1')
        # De 2 a 52. Nombre del Ordenante
        text += self.convert(self.company_partner_bank_id.partner_id.name, 50)
        # De 52 a 67. NIF contrato confirming
        vat = self.convert_vat(self.company_partner_bank_id.partner_id)
        text += self.convert(vat, 15)
        # De 67 a 75. Fecha de proceso del fichero. Fecha en que se paga a los proveedoes.
        date_file = fields.Date.from_string(self.date_scheduled).strftime('%Y%m%d')
        text += date_file
        # De 75 a 83. Fecha de la remesa. Fecha de generación del fichero.
        text += date_file
        # De 83 a 103. Código activo de contrato de Bankinter
        text += self.convert(self.payment_mode_id.num_contract, 20)
        # De 103 a 137. Cuenta de cargo IBAN.
        cuenta = self.company_partner_bank_id.acc_number
        cuenta = cuenta.replace(' ', '')
        tipo_cuenta = self.company_partner_bank_id.acc_type
        if tipo_cuenta != 'iban':
            raise UserError(
                _("Error: El tipo de cuenta de %s debe tener formato IBAN.") % cuenta)
        text += self.convert(cuenta, 34)
        # De 137 a 140. Código divisa
        text += self.company_currency_id.name
        # De 140 a 141. Tipo de pago. Confirming => '2'
        text += '2'
        # De 141 a 171. Referencia del fichero
        text += self.convert(self.name, 30)
        # De 171 a 173. Tipo de formato. Texto "FU"
        text += 'FU'
        # De 173 a 250. Blancos
        text = text.ljust(250) + '\r\n'
        all_text = text

        return all_text

    def _group_by_partner(self, lines):
        grouped_lines = {}
        for l in lines:
            if l.partner_id not in grouped_lines:
                grouped_lines[l.partner_id] = []
            grouped_lines[l.partner_id] += l
        return grouped_lines

    def _pop_detalle_sabadell(self, line):
        """
        """
        all_text = ''

        for pl in line.payment_line_ids:
            for i in range(4):    
                if(i + 3) == 3:
                    # De 1 a 1. Número de registro
                    text = self._get_fix_part_sabadell('3')
                    # De 2 a 72. Nombre del proveedor
                    name = line['partner_id']['name']
                    text += self.convert(name, 70)
                    # De 72 a 92. NIF
                    nif = line['partner_id']['vat']
                    if not nif:
                        raise UserError(
                            _("Error: El Proveedor %s no tiene \
                                establecido el NIF.") % line['partner_id']['name'])
                    text += self.convert(nif[2:], 20)
                    # De 92 a 157. Domicilio proveedor
                    domicilio_pro = line['partner_id']['street']
                    if not domicilio_pro:
                        raise UserError(
                            _("Error: El Proveedor %s no tiene\
                            establecido el Domicilio.\
                            ") % line['partner_id']['name'])
                    text += self.convert(domicilio_pro, 65)
                    # De 157 a 197. Población proveedor
                    ciudad_pro = line['partner_id']['city']
                    if not ciudad_pro:
                        raise UserError(
                            _("Error: El Proveedor %s no tiene establecida\
                                                            la Ciudad.") % line['partner_id']['name'])
                    text += self.convert(ciudad_pro, 40)
                    # De 197 a 207. Código postal proveedor
                    cp_pro = line['partner_id']['zip']
                    if not cp_pro:
                        raise UserError(
                            _("Error: El Proveedor %s no tiene establecido\
                                                                el C.P.") % line['partner_id']['name'])
                    text += self.convert(cp_pro, 10)
                    # De 207 a 209. País proveedor
                    pais = line.partner_id.country_id
                    if not pais:
                        raise UserError(
                            _("Error: El Proveedor %s no tiene establecida\
                            el Pais.") % line['partner_id']['name'])
                    text += pais.code
                    # De 209 a 250.
                    # Lo trato en el if (i + 3) != 6

                if (i + 3) == 4:
                    # De 1 a 1. Número de registro
                    text = self._get_fix_part_sabadell('4')
                    # De 2 a 50
                    email = line['partner_id']['email']
                    if not email:
                        raise UserError(
                            _("Error: El Proveedor %s no tiene\
                                            email.\
                                            ") % line['partner_id']['name'])
                    text += self.convert(email, 50)
                    # De 50 a 250. Blancos
                    # Lo trato en el if (i + 3) != 6

                if (i + 3) == 5:
                    # De 1 a 2. Número de registro
                    text = self._get_fix_part_sabadell('5')
                    # De 2 a 3. Forma de pago. Transferencia => 'T'
                    text += 'T'
                    # De 3 a 37. IBAN
                    cuenta = line.partner_bank_id.acc_number
                    cuenta = cuenta.replace(' ', '')
                    text += self.convert(cuenta, 34)
                    # De 37 a 48. BIC
                    if line.partner_bank_id.bank_id and \
                            line.partner_bank_id.bank_id.bic:
                        text += self.convert(line.partner_bank_id.bank_id.bic,11)
                    else:
                        text += 11 * ' '
                    # De 48 a 82. Cuenta para pagos internacionales fuera zona SEPA
                    text += ' ' * 34
                    # De 82 a 84. Código País banco. Sólo pagos internacionales
                    text += ' ' * 2
                    # De 84 a 95. Codigo ABA
                    text += ' ' * 11
                    # De 95 a 97. Tipo proveedor
                    text += ' ' * 2
                    # De 97 a 137. Por cuenta de
                    text += ' ' * 40
                    # De 137 a 250. Blancos
                    # Lo trato en el if (i + 3) != 6

                if (i + 3) == 6:
                    inv = pl.move_line_id.invoice_id
                    # De 1 a 2.
                    text = self._get_fix_part_sabadell('6')
                    # De 2 a 22. Número de factura.
                    text += self.convert(pl.communication, 20)
                    # De 22 a 23. Signo
                    text += '+' if pl.amount_currency >= 0 else '-'
                    # De 23 a 38. Importe factura
                    self.importe_remesa += pl.amount_currency
                    amount = "{:.2f}".format((abs(pl.amount_currency)))
                    amount = amount.replace('.', '')
                    text += amount.rjust(15, '0')
                    # De 38 a 46. Fecha de emisión
                    if inv.date_invoice:
                        fecha_factura = inv.date_invoice.replace('-', '')
                        dia = fecha_factura[6:]
                        mes = fecha_factura[4:6]
                        ano = fecha_factura[:4]
                        fecha_factura = ano + mes + dia
                    else:
                        fecha_factura = fields.Date.from_string(
                            pl.move_line_id.
                                date).strftime('%Y%m%d')
                    if inv.date_invoice > self.date_scheduled:
                        raise UserError(
                            _("Error: La factura %s tiene una fecha mayor que \
                            La remesa") % inv.number)
                    text += fecha_factura
                    # De 46 a 54. Fecha d evencimiento. Postfinanciación.
                    date_post_finan = fields.Date.from_string(self.post_financing_date) \
                        .strftime('%Y%m%d')
                    text += date_post_finan
                    # De 54 a 62. Fecha de prórroga aplazamiento.
                    text += ' ' * 8
                    # De 62 a 78. Referencia de pago para conciliación norma 43. L\d{5}
                    # Tratamos todo conjuntamente

                text = text.ljust(250) + '\r\n'
                all_text += text

        return all_text

    def _pop_totales_sabadell(self):

        # De 1 a 2.
        text = self._get_fix_part_sabadell('7')
        # De 2 a 14. Total valores de registro tipo 3
        text += str(self.num_records).rjust(12, "0")
        # De 14 a 29. Total importes
        text += "{:.2f}".format(round(self.importe_remesa,2)).replace('.', '').rjust(15, '0')
        # De 29 a 250. Blancos
        text = text.ljust(250) + '\r\n'

        return text
