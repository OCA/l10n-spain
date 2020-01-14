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
        if self.payment_method_id.code != 'conf_bbva':
            return super(AccountPaymentOrder, self).generate_payment_file()
        if self.date_prefered != 'fixed':
            raise UserError(_('Solo fecha fija'))
        self.num_records = 0
        self.total_pos_amount = 0
        self.total_neg_amount = 0
        txt_file = self._pop_cabecera_bbva()
        grouped_lines = self._group_by_partner(self.bank_line_ids)
        for partner in grouped_lines:
            lines = grouped_lines[partner]
            for line in lines:
                txt_file += self._pop_detalle_bbva(line)
        txt_file += self._pop_totales_bbva()
        # txt_file = self.ensure_valid_ascii(txt_file)
        return str.encode(txt_file, encoding='cp1252', errors='replace'), self.name + '.BBVA'

    def _get_fix_part(self, cr, cd):
        self.num_records += 1
        text = ''
        # 1 a 3 Código de registro
        text += cr
        # 4 - 6 Codigo de Dato
        text += cd
        # 7 - 31 Codigo ordenante
        vat = self.convert_vat(self.company_partner_bank_id.partner_id)
        text += self.convert(vat, 25)

        # 32 - 34 Sufijo presentador
        text += self.payment_mode_id.sufix or '000'

        num_dato = str(self.num_records)
        # 35 - 40 Numero del dato
        text += num_dato.rjust(6, '0')
        return text

    def _pop_cabecera_bbva(self):
        all_text = ''
        text = self._get_fix_part('010', '010')

        # 41 - 48 Fecha de envío del fichero
        date_file = fields.Date.from_string(self.date_scheduled)\
            .strftime('%d%m%Y')
        text += date_file
        # 40 - 52 Código banco
        text += '0182'
        # 53 - 112 Nombre Presentador
        text += self.convert(self.company_partner_bank_id.partner_id.name, 60)
        # 113 - 122 Referencia Fichero
        text += self.convert(self.name, 10)
        # 123 - 150 Libre
        text += 28 * ' '
        all_text += text.ljust(150)+'\r\n'

        # PRIMER REGISTRO CABECERA ORDENANTE
        text = self._get_fix_part('020', '010')
        # import pdb; pdb.set_trace()
        # 41 - 48 Fecha de envio del fichero
        # date_now = time.strftime('%d%m%Y')
        # date_file = fields.Date.from_string(self.date_generated)\
        #     .strftime('%d%m%Y')
        text += date_file
        # 49 - 56 Fecha de la remesa
        # date_pos = fields.Date.from_string(self.post_financing_date)\
        #     .strftime('%d%m%Y')
        text += date_file

        # 57 - 90 IBAN ORDENANTE
        cuenta = self.company_partner_bank_id.acc_number
        cuenta = cuenta.replace(' ', '')
        # tipo_cuenta = self.company_partner_bank_id.acc_type
        # if tipo_cuenta == 'iban':
        #     cuenta = cuenta[4:]
        # # control = cuenta[8:10]
        # principio = cuenta[:8]
        # cuenta = principio + cuenta[10:]
        text += self.convert(cuenta, 34)

        # 91 - 98 Referencia ordenante (num contrato confirming)
        text += self.payment_mode_id.num_contract \
            if self.payment_mode_id.num_contract else 8 * ' '

        # 99 -108 Referencia de remesa del ordenante (opcional)
        text += self.name.rjust(10)
        # 109 -150 Libre
        text += 42 * ' '
        all_text += text.ljust(150)+'\r\n'

        # SEGUNDO REGISTRO CABECERA ORDENANTE
        text = self._get_fix_part('020', '020')
        # 41 - 100 Nombre Presentador
        text += self.convert(self.company_partner_bank_id.partner_id.name, 60)
        # 100 - 101 Seguro de cambio (opcional)
        text += ' '
        # 102 -150 Libre
        text += 49 * ' '

        all_text += text.ljust(150)+'\r\n'
        return all_text

    def _group_by_partner(self, lines):
        grouped_lines = {}
        for l in lines:
            if l.partner_id not in grouped_lines:
                grouped_lines[l.partner_id] = []
            grouped_lines[l.partner_id] += l
        return grouped_lines

    def _pop_detalle_bbva(self, line):
        """
        """
        all_text = ''
        # import pdb; pdb.set_trace()
        for i in range(5):
            text = ''
            if (i + 1) == 1:
                text = self._get_fix_part('030', '010')
                # 41 - 65 NIF BENEFICIARIO
                nif = line['partner_id']['vat']
                if not nif:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene \
                            establecido el NIF.") % line['partner_id']['name'])
                text += self.convert(nif[2:], 25)
                # 66 - 68 SUFIJO BENEFICIARIO
                text += '000'
                # 69 - 128 NOMBRE DEL BENEFICIARIO
                name = line['partner_id']['name']
                text += self.convert(name, 60)
                # 129 - 129 CLASIFICACIÓN OPCIONAL
                text += 'A'
                # 130 -150 Libre
                text += 21 * ' '

            if (i + 1) == 2:
                text = self._get_fix_part('030', '020')
                # 41 - 76 Domicilio Fiscal
                domicilio_pro = line['partner_id']['street']
                if not domicilio_pro:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene\
                         establecido el Domicilio.\
                         ") % line['partner_id']['name'])
                text += self.convert(domicilio_pro, 36)
                # 77 - 150 Libre
                text += 74 * ' '

            if (i + 1) == 3:
                text = self._get_fix_part('030', '021')
                # 41 - 47 CÓDIGO POSTAL
                cp_pro = line['partner_id']['zip']
                if not cp_pro:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene establecido\
                         el C.P.") % line['partner_id']['name'])
                text += self.convert(cp_pro, 7)
                # 48 - 75 POBLACION
                ciudad_pro = line['partner_id']['city']
                if not ciudad_pro:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene establecida\
                         la Ciudad.") % line['partner_id']['name'])
                text += self.convert(ciudad_pro, 28)
                # 76 - 95 PROVINCIA
                provincia = line['partner_id']['state_id']
                if not provincia:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene establecida\
                         la provincia.") % line['partner_id']['name'])

                provincia = line.partner_id.state_id.name
                text += self.convert(provincia, 20)
                # 96 - 115 PAIS
                pais = line.partner_id.country_id
                if not pais:
                    raise UserError(
                        _("Error: El Proveedor %s no tiene establecida\
                         el Pais.") % line['partner_id']['name'])
                text += self.convert(pais.name, 20)
                # 116 - 117 CÓDIGO ISO ALFA
                text += pais.code
                # 118 - 150 LIBRE
                text += 33 * ' '

            if (i + 1) == 4:
                text = self._get_fix_part('030', '050')

                # 57 - 90 IBAN ORDENANTE
                cuenta = line.partner_bank_id.acc_number
                cuenta = cuenta.replace(' ', '')

                # 41 - 74 IBAN BENEFICIARIO
                text += self.convert(cuenta, 34)
                # BIC BANCO SI NO IBANO LIBRE
                if line.partner_bank_id.bank_id and \
                        line.partner_bank_id.bank_id.bic:
                    text += line.partner_bank_id.bank_id.bic
                else:
                    text += 11 * ' '
                # LIBRE
                text += 65 * ' '

            if (i + 1) == 5:
                for pl in line.payment_line_ids:
                    inv = pl.move_line_id.invoice_id
                    text = self._get_fix_part('040', '020')
                    # 41 - 58 REFERENCIA ORDEN PAGO
                    text += self.convert(pl.name, 18)
                    # 59 - 78 N FACTURA
                    text += self.convert(pl.communication, 20)
                    # 79 - 86 FECHA FACTURA
                    # 31 - 36: Fecha factura
                    fecha_factura = 6 * ' '
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
                    # 87 - 94 FECHA DE VENCIMIENTO
                    # fecha_vencimiento = pl.ml_maturity_date.replace('-', '')
                    # fecha_vencimiento = pl.ml_maturity_date.replace('-', '')
                    # dia = fecha_vencimiento[6:]
                    # mes = fecha_vencimiento[4:6]
                    # ano = fecha_vencimiento[:4]
                    # fecha_vencimiento = dia + mes + ano
                    new_due_date = fields.Datetime.from_string(
                        self.date_scheduled) + datetime.timedelta(days=3)
                    fecha_vencimiento = new_due_date.strftime('%d%m%Y')
                    fecha_vencimiento2 = new_due_date.strftime('%Y-%m-%d')

                    if fecha_vencimiento2 > self.post_financing_date:
                        raise UserError(
                            _("Error: La fecha de vencimiento no puede ser \ayor que la fecha de cargo (fecha post financiación)"))

                    text += fecha_vencimiento
                    # 95 - 95 SIGNO
                    sign = '+' if pl.amount_currency >= 0 else '-'
                    text += sign
                    # 96 - 110 IMPORTE
                    if pl.amount_currency >= 0:
                        self.total_pos_amount += abs(pl.amount_currency)
                    else:
                        self.total_neg_amount += abs(pl.amount_currency)
                    
                    amount = "{:.2f}".format((abs(pl.amount_currency)))
                    amount = amount.replace('.', '')
                    text += amount.rjust(15, '0')
                    # 111 - 113 DIVISA (Ajustado drtcha, ceros izq,
                    #                  13 enteros, dos decimales)
                    text += inv.currency_id.name
                    # 114 - 114 Forma de pago (opcional)
                    text += 1 * ' '
                    # 115 - 122 FECHA CARGO CLIENTE
                    text += 8 * ' '
                    # 118 - 150 LIBRE
                    text += 28 * ' '
                    text = text.ljust(150)+'\r\n'
                    all_text += text
            if (i + 1) != 5:
                text = text.ljust(150)+'\r\n'
                all_text += text
        return all_text

    def _pop_totales_bbva(self):
        text = self._get_fix_part('050', '090')
        # 41 - 46 N TOTAL REGISTROS
        n_record = str(self.num_records - 1)
        text += n_record.rjust(6, '0')
        # 47 - 64 SUMATORIO IMPORTES POSITIVOS
        pos = "{:.2f}".format(self.total_pos_amount).replace('.', '')
        text += pos.rjust(18, '0')
        # 45 - 82 SUMATORIO IMPORTES NEGATIVOS
        neg = "{:.2f}".format(self.total_neg_amount).replace('.', '')
        text += neg.rjust(18, '0')
        # 83 - 150 LIBRE
        text += 68 * ' '
        text = text.ljust(150)+'\r\n'

        text += self._get_fix_part('050', '099')
        # 41 - 46 N TOTAL REGISTROS
        n_record = str(self.num_records)
        text += n_record.rjust(6, '0')
        # 47 - 64 SUMATORIO IMPORTES POSITIVOS
        # pos = str(self.total_pos_amount).replace('.', '')
        text += pos.rjust(18, '0')
        # 45 - 82 SUMATORIO IMPORTES NEGATIVOS
        # neg = str(self.total_neg_amount).replace('.', '')
        text += neg.rjust(18, '0')
        # 83 - 150 LIBRE
        text += 68 * ' '
        text = text.ljust(150)+'\r\n'

        return text
