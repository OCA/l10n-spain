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
        if self.payment_method_id.code != 'conf_abanca':
            return super(AccountPaymentOrder, self).generate_payment_file()
        if self.date_prefered != 'fixed':
            raise UserError(_('Solo fecha fija'))
        # ##################################################
        # ##################################################
        # número de orden de cada pago
        self.num_pago = 0
        # Importe total de la remesa
        self.importe_remesa = 0
        # ##################################################
        # ##################################################
        self.num_records = 0

        txt_file = self._pop_cabecera_abanca()
        grouped_lines = self._group_by_partner(self.bank_line_ids)
        for partner in grouped_lines:
            lines = grouped_lines[partner]
            for line in lines:
                txt_file += self._pop_detalle_abanca(line)
        txt_file += self._pop_totales_abanca()
        # txt_file = self.ensure_valid_ascii(txt_file)
        return str.encode(txt_file, encoding='cp1252', errors='replace'), self.name + '.Q17'

    def _get_fix_part_abanca(self, cr):
        self.num_records += 1
        text = ''
        # 1 a 2 código del registro
        text += cr
        # Si es el registro de cabecera (10) La parte numérica del nombre de la orden de pago PAY(\d{5})
        # En caso contraro 12 posiciones a blancos.
        text += self.name[3:].rjust(12,'0') if cr == "10" else ' ' * 12

        return text

    def _pop_cabecera_abanca(self):

        all_text = ''
        text = self._get_fix_part_abanca('10')

        # 15 a 24 Libre. Numérico con relleno a 0's
        text += "0" * 9
        # 24 a 25. Alfanumérico. Libre 2
        text += ' '
        # 25 a 40. Número de contrato Númérico
        text += self.payment_mode_id.num_contract.rjust(15,"0")
        # 40 a 50. Numérico. Libre 3
        text += '0' * 10
        # 50 a 51. Alfanumérico. Libre 4
        text += ' '
        # 51 a 59. Fecha Remesa
        date_file = fields.Date.from_string(self.date_scheduled)\
            .strftime('%d%m%Y')
        text += date_file
        # 59 a 62. Moneda ISO (EUR)
        text += self.company_currency_id.name
        # 62 a 63. Alfanumérico. Libre 5
        text += ' '
        # 63 a 68. Numérico. Libre 6
        text += ' ' * 5
        # 68 a 83. Alfanumérico. NIF Rías
        vat = self.convert_vat(self.company_partner_bank_id.partner_id)
        text += self.convert(vat, 15)
        # 83 a 123. Alfanumérico. Nombre empresa.
        text += self.convert(self.company_partner_bank_id.partner_id.name, 40)
        # 123 a 127. IBAN cuenta de cargo. + 127 a 157 CCC
        cuenta = self.company_partner_bank_id.acc_number
        cuenta = cuenta.replace(' ', '')
        text += self.convert(cuenta, 34)
        # 157 a 351. Alfanumérico. Libre 7.
        text = text.ljust(351)+'\r\n'
        all_text += text
        return all_text

    def _group_by_partner(self, lines):
        grouped_lines = {}
        for l in lines:
            if l.partner_id not in grouped_lines:
                grouped_lines[l.partner_id] = []
            grouped_lines[l.partner_id] += l
        return grouped_lines

    def _pop_detalle_abanca(self, line):
        """
        """
        suma_recibos = 0
        all_text = ''
        # import pdb; pdb.set_trace()
        for i in range(3):
            text = ''
            if (i + 1) == 1:
                self.num_pago += 1
                text = self._get_fix_part_abanca('20')
                # 15 a 24. Nümero de pago
                text += str(self.num_pago).rjust(9,"0")
                # 24 a 25. Forma de Pago => Confirming Pronto Pago = "I"
                text += 'I'
                # 25 a 26. Indicador a la orden o no a la orden. Blanco
                text += ' '
                # 26 a 27. Indicador de logo. Blanco
                text += ' '
                # 27 a 28. Indicadro de firma digital. Blanco
                text += ' '
                # 28 a 29. Indicador de entrega a proveedor o a cliente. Blanco
                text += ' '
                # 29 a 36. Número de pago único Q43.
                text += self.convert(line.name, 7)
                # 36 a 51. Importe del pago agrupado.
                self.importe_remesa += line.amount_currency
                amount = "{:.2f}".format(line.amount_currency)
                amount = amount.replace('.', '')
                text += amount.rjust(15, '0')
                # 51 a 59. Fecha vto pago
                date_post_finan = fields.Date.from_string(self.post_financing_date) \
                    .strftime('%d%m%Y')
                text += date_post_finan
                # 59 a 60. Anulación Orden
                text += ' '
                # 60 a 61. Gastos de la orden. '3' => Compartidos
                text += '3'
                # 61 a 62. Tipo estadístico. 'M' => Pago de mercancía
                text += 'M'
                # 62 a 68. Partida estadística. Obligatorio para pagos transfronterizos superiores a 12.500,00Eur.
                # Nosotros sólo vamos a hacer pagos nacionales.
                text += ' ' * 6
                # 68 a 83. NIF beneficiario
                nif = line['partner_id']['vat']
                if not nif:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene \
                            establecido el NIF.") % line['partner_id']['name'])
                text += self.convert(nif[2:], 15)
                # 83 a 123. Nombre del Beneficiario
                name = line['partner_id']['name']
                text += self.convert(name, 40)
                # 123 a 127 y 127 a 157. IBAN beneficiario.
                cuenta = line.partner_bank_id.acc_number
                cuenta = cuenta.replace(' ', '')
                text += self.convert(cuenta, 34)
                # 157 a 197. Nombre banco beneficiario
                text += ' ' * 40
                # 197 a 209. BIC banco beneficiario
                if line.partner_bank_id.bank_id and \
                        line.partner_bank_id.bank_id.bic:
                    text += self.convert(line.partner_bank_id.bank_id.bic, 12)
                else:
                    text += 12 * ' '
                # 209 a 210. Idioma comunicación al beneficiario. 'E'
                text += 'E'
                # 210 a 212. Libre 3
                text += ' ' * 2
                # 212 a 220. Fcha Vto plus
                text += ' ' * 8
                # 220 a 351
                text = text.ljust(351) + '\r\n'

            if (i + 1) == 2:
                text = self._get_fix_part_abanca('21')
                # 15 a 24. Nümero de pago
                text += str(self.num_pago).rjust(9,"0")
                # 24 a 64. Vía pública del beneficiario.
                domicilio_pro = line['partner_id']['street']
                if not domicilio_pro:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene\
                         establecido el Domicilio.\
                         ") % line['partner_id']['name'])
                text += self.convert(domicilio_pro, 40)
                # 64 a 89. Localidad del beneficiario
                ciudad_pro = line['partner_id']['city']
                if not ciudad_pro:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene establecida\
                                         la Ciudad.") % line['partner_id']['name'])
                text += self.convert(ciudad_pro, 25)
                # 89 a 114. Provincia del beneficiario
                provincia = line['partner_id']['state_id']
                if not provincia:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene establecida\
                                         la provincia.") % line['partner_id']['name'])

                provincia = line.partner_id.state_id.name
                text += self.convert(provincia, 25)
                # 114 a 124. Código postal beneficiario
                cp_pro = line['partner_id']['zip']
                if not cp_pro:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene establecido\
                         el C.P.") % line['partner_id']['name'])
                text += self.convert(cp_pro, 10)
                # 124 a 126. País del beneficiario
                pais = line.partner_id.country_id
                if not pais:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene establecida\
                         el Pais.") % line['partner_id']['name'])
                text += pais.code
                # 126 a 166. Vía pública banco beneficiario
                text += ' ' * 40
                # 166 a 191. Localidad banco beneficiario
                text += ' ' * 25
                # 191 a 216. Provincia banco beneficiario
                text += ' ' * 25
                # 216 a 226. Código postal banco beneficiario
                text += ' ' * 10
                # 226 a 228. país banco beneficiario
                text += ' ' * 2
                # 228 a 242. Teléfono beneficiario
                text += ' ' * 14
                # 242 a 256. Fax beneficiario
                text += ' ' * 14
                # 256 a 351 E-mail beneficiario
                text = text.ljust(351) + '\r\n'

            if (i + 1) == 3:

                for pl in line.payment_line_ids:
                    inv = pl.move_line_id.invoice_id
                    text = self._get_fix_part_abanca('30')
                    # 15 a 24. Nümero de pago
                    text += str(self.num_pago).rjust(9, "0")
                    # De 24 a 25. Tipo de documento. F si factura y A si abono
                    text += 'F' if pl.amount_currency >= 0 else 'A'
                    # De 25 a 35. Número de documento.
                    text += self.convert(pl.communication, 10)
                    # De 35 a 50. Importe documento
                    suma_recibos += pl.amount_currency
                    amount = "{:.2f}".format((abs(pl.amount_currency)))
                    amount = amount.replace('.', '')
                    text += amount.rjust(15, '0')
                    # De 50 a 51 Signo
                    text += 'P' if pl.amount_currency >= 0 else 'N'
                    # De 51 a 59. Fecha factura
                    if inv.date_invoice:
                        fecha_factura = inv.date_invoice.replace('-', '')
                        dia = fecha_factura[6:]
                        mes = fecha_factura[4:6]
                        ano = fecha_factura[:4]
                        fecha_factura = dia + mes + ano
                    else:
                        fecha_factura = fields.Date.from_string(
                            pl.move_line_id.
                            date).strftime('%d%m%Y')
                    if inv.date_invoice > self.date_scheduled:
                        raise UserError(
                            _("Error: La factura %s tiene una fecha mayor que \
                              La remesa") % inv.number)
                    text += fecha_factura
                    # De 59  a 351
                    text = text.ljust(351) + '\r\n'
                    # Para los registros tipo 30 detalle de factura. Voy añadiendo la línea a all_text
                    # según la voy tratando.
                    all_text += text
            # Para los registros 20 y 21 añado la línea a all_text
            if (i+1 !=3):
                all_text += text

        #if suma_recibos != line.amount_currency:
        #    raise UserError(
        #        _("Error: La suma de los recibos no coincie con el importe del pago agrupado."))

        return all_text

    def _pop_totales_abanca(self):
        text = self._get_fix_part_abanca('90')
        # De 15 a 24. Número total de pagos
        text += str(self.num_pago).rjust(9, "0")
        # De 24 a 25. Libre 2
        text += ' '
        # De 25 a 35. Número total de registros.
        n_record = str(self.num_records)
        text += n_record.rjust(10, '0')
        # De 35 a 50. Importe total remesa.
        text += "{:.2f}".format(round(self.importe_remesa, 2)).replace('.', '').rjust(15, '0')
        # De 50 a 351. Libre 3
        text = text.ljust(351) + '\r\n'

        return text
