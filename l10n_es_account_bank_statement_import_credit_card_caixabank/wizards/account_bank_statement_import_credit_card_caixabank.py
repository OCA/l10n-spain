# Copyright 2018 Tecnativa - Pedro Baeza
# Copyright 2018 Eficent - Jordi Ballester Alomar
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, exceptions, _
from datetime import datetime

account_mapping = {
    '01': '4300%00',
    '02': '4100%00',
    '03': '4100%00',
    '04': '430%00',
    '05': '6800%00',
    '06': '6260%00',
    '07': '5700%00',
    '08': '6800%00',
    '09': '2510%00',
    '10': '5700%00',
    '11': '5700%00',
    '12': '5700%00',
    '13': '5730%00',
    '14': '4300%00',
    '15': '6400%00',
    '16': '6690%00',
    '17': '6690%00',
    '98': '5720%00',
    '99': '5720%00',
}


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    def _process_record_0010(self, line):
        """Cabecera (Tipo registro '00'-'10')"""
        c1 = 4        # TCRTPCT + TCRSUBT
        c2 = c1+30  # TCRDOCU
        c3 = c2+16  # TCRDNIC
        c4 = c3+52  # TCRNOMC
        c5 = c4+28  # TCRDEPA
        c6 = c5+15  # TCRCONT
        c7 = c6+16  # TCRNPAN
        c8 = c7+8   # TCRFINI
        c9 = c8+8   # TCRFFIN
        c10 = c9+3  # TCRORDE
        c11 = c10+1   # TCRCRED
        c12 = c11+1   # TCRDEBI
        c13 = c12+1   # TCRCONS
        c14 = c13+1   # TCRRCAR

        st_cabecera = {
            'tipo_documento': line[c1:c2],
            'nif_titular': line[c2:c3],
            'nombre_titular': line[c3:c4],
            'departamento': line[c4:c5],
            'contrato': line[c5:c6],
            'tarjeta': line[c6:c7],
            'fecha_inicio_pet_rel_op': datetime.strptime(line[c7:c8],
                                                         '%d%m%Y').date(),
            'fecha_fin_pet_rel_op': datetime.strptime(line[c8:c9],
                                                      '%d%m%Y').date(),
            'criterio_ordenacion': line[c9:c10],
            'solicitadas_operaciones_credito': line[c10:c11],
            'solicitadas_operaciones_debito': line[c11:c12],
            'solicitadas_operaciones_consumos_prepago': line[c12:c13],
            'solicitadas_operaciones_recarga': line[c13:c14],
            'contratos': [],
        }
        return st_cabecera

    def _process_record_0020(self, line):
        """Contrato (Tipo registro '00'-'20')"""
        c1 = 4          # TCRTPCT + TCRSUBT
        c2 = c1+15      # TCRIDEX CHAR(15)
        c3 = c2+15      # TCRCTE CHAR(15)
        c4 = c3+22      # TCRTARG CHAR(22)
        c5 = c4+30      # TCRAFFI CHAR(30)
        c6 = c5+5       # TCRENTI PIC'(5)9'
        c7 = c6+5       # TCROFIC PIC'(5)9'
        c8 = c7+1       # TCRDIG1 PIC'9'
        c9 = c8+1       # TCRDIG2 PIC'9'
        c10 = c9+11     # TCRCTA PIC'(11)9'
        c11 = c10+3     # TCRMONC CHAR(3)
        c12 = c11+9+2     # TCRLIMC PIC'(9)9V99'
        c13 = c12+1+8+2     # TCRDISP PIC'-(8)9V99'

        st_contrato = {
            'identificador_expediente': line[c1:c2],
            'identificador_contrato': line[c2:c3],
            'identificador_tarjeta': line[c3:c4],
            'descripcion_affinity': line[c4:c5],
            'entidad_deposito_cargo': line[c5:c6],
            'oficina_deposito_cargo': line[c6:c7],
            'digito_1_deposito_cargo': line[c7:c8],
            'digito_2_deposito_cargo': line[c8:c9],
            'cuenta_deposito_cargo': line[c9:c10],
            'moneda_contrato': line[c10:c11],
            'limite_contrato': line[c11:c12],
            'disponible_contrato': line[c12:c13],
            'tarjetas': [],
        }
        return st_contrato

    def _process_record_0030(self, line):
        """Cabecera tarjeta (Tipo registro '00'-'30')"""
        c1 = 4          # TCRTPCT + TCRSUBT
        c2 = c1+15      # TCRIDEX CHAR(15)
        c3 = c2+15      # TCRCTE CHAR(15)
        c4 = c3+22      # TCRTARG CHAR(22)
        c5 = c4+30      # TCRAFFI CHAR(30)
        c6 = c5+52      # TCRNOMT CHAR(52)
        c7 = c6+5       # TCRENTI PIC'(5)9'
        c8 = c7+5       # TCROFIC PIC'(5)9'
        c9 = c8+1       # TCRDIG1 PIC'9'
        c10 = c9+1      # TCRDIG2 PIC'9'
        c11 = c10+11    # TCRCTA PIC'(11)9'
        c12 = c11+3     # TCRMONT CHAR(3)
        c13 = c12+9+2     # TCRLIMC PIC'(9)9V99'
        c14 = c13+1+8+2     # TCRDISP PIC'-(8)9V99'

        st_tarjeta = {
            'identificador_expediente': line[c1:c2],
            'identificador_contrato': line[c2:c3],
            'identificador_tarjeta': line[c3:c4],
            'descripcion_affinity': line[c4:c5],
            'entidad_deposito_cargo': line[c5:c6],
            'titular_tarjeta': line[c5:c6],
            'oficina_deposito_cargo': line[c7:c8],
            'digito_1_deposito_cargo': line[c8:c9],
            'digito_2_deposito_cargo': line[c9:c10],
            'cuenta_deposito_cargo': line[c10:c11],
            'moneda_tarjeta': line[c11:c12],
            'limite_tarjeta': line[c12:c13],
            'disponible_tarjeta': line[c13:c14],
            'operaciones': [],
        }
        return st_tarjeta

    def _process_record_1010(self, line):
        """operaciones (Tipo registro '10'-'10')"""
        c1 = 4              # TCRTPCT + TCRSUBT
        c2 = c1+8           # TCRPERL PIC'(8)9'
        c3 = c2+15          # TCRIDEX CHAR(15)
        c4 = c3+15          # TCRCTE CHAR(15)
        c5 = c4+22          # TCRTARG CHAR(22)
        c6 = c5+25          # TCRREFE CHAR(25)
        c7 = c6+8           # TCRFECH PIC'(8)9'
        c8 = c7+9           # TCRCODC PIC'(9)9'
        c9 = c8+40          # TCRNCOM CHAR(40)
        c10 = c9+25         # TCRLOCC CHAR(25)
        c11 = c10+3         # TCRMONO CHAR(3)
        c12 = c11+1+10+2      # TCRIMPOR PIC'-(10)9V99'
        c13 = c12+1+10+2      # TCRIMCTE PIC'-(10)9V99
        c14 = c13+1         # TCRINDB CHAR(1)
        c15 = c14+3         # TCRTIPB PIC'999'
        c16 = c15+1+10+2      # TCRIMBO PIC'-(10)9V99'
        c17 = c16+5         # TCRCODR PIC'(5)9'
        c18 = c17+20        # TCRNOMR CHAR(20)
        c19 = c18+3         # TCRPASO CHAR(3)
        c20 = c19+3         # TCRMORIG CHAR(3)
        c21 = c20+13        # TCRTLFO CHAR(13)
        c22 = c21+16        # TCRNIFC CHAR(16)
        c23 = c22+52        # TCRDIRC CHAR(52)
        c24 = c23+5         # TCRPOST PIC'(5)9'
        c25 = c24+1+4+2       # TCRIMCO PIC'-(4)9V99'
        c26 = c25+11        # TCRRES3 CHAR(11)

        st_tarjeta = {
            'fecha_periodo_liquidacion': line[c1:c2],
            'identificador_expediente': line[c2:c3],
            'identificador_contrato': line[c3:c4],
            'identificador_tarjeta': line[c4:c5].strip(),
            'fecha_intercambio': line[c5:c6],
            'fecha_operacion': datetime.strptime(line[c6:c7], '%d%m%Y').date(),
            'codigo_comercio': line[c7:c8].strip(),
            'nombre_comercio': line[c8:c9].strip(),
            'localidad_comercio': line[c9:c10].strip(),
            'moneda_operacion': line[c10:c11].strip(),
            'importe_origen': -1 * float("%s.%s" % (
                line[c11:c11+1+10], line[c11+1+10:c11+1+10+2])),
            'importe_operacion_moneda_contrato': -1 * float("%s.%s" % (
                line[c12:c12+1+10], line[c12+1+10:c12+1+10+2])),
            'indicador_bonificacion': line[c13:c14],
            'tipo_bonificacion': line[c14:c15],
            'importe_bonificado': line[c15:c16],
            'codigo_ramo': line[c16:c17],
            'nombre_ramo': line[c17:c18],
            'pais_operacion': line[c18:c19],
            'moneda_original_operacion': line[c19:c20].strip(),
            'nif': line[c20:c21].strip(),
            'nif_comercio': line[c21:c22].strip(),
            'domicilio_comercio': line[c22:c23],
            'codigo_postal': line[c23:c24].strip(),
            'importe_comision': float("%s.%s" % (
                line[c24:c24+1+4], line[c24+1+4:c24+1+4+2])),
            'reserva': line[c25:c26],
            'addendums': [],
        }
        return st_tarjeta

    def _parse_cc_caixabank(self, data_file):
        # st_data will contain data read from the file
        st_data = {
            '_num_records': 0,  # Number of records really counted
            'cabecera': [],
        }
        st_cabecera = []
        st_contratos = []
        st_tarjetas = []
        for raw_line in data_file.split("\n"):
            if not raw_line.strip():
                continue
            code = raw_line[0:4]
            if code == '0010':
                st_cabecera = self._process_record_0010(raw_line)
                st_data['cabecera'].append(st_cabecera)
            elif code == '0020':
                st_contratos = self._process_record_0020(raw_line)
                st_cabecera['contratos'].append(st_contratos)
            elif code == '0030':
                st_tarjetas = self._process_record_0030(raw_line)
                st_contratos['tarjetas'].append(st_tarjetas)
            elif code == '1010':
                st_operaciones = self._process_record_1010(raw_line)
                st_tarjetas['operaciones'].append(st_operaciones)
            elif code == '1020':
                # TODO
                continue
            elif code == '9930':
                # TODO
                continue
            elif code == '9920':
                # TODO
                continue
            elif code == '9910':
                # TODO
                continue
            elif ord(raw_line[0]) == 26:  # pragma: no cover
                # CTRL-Z (^Z), is often used as an end-of-file marker in DOS
                continue
            else:
                raise exceptions.ValidationError(
                    _('Record type %s is not valid.') % raw_line[0:4])
            # Update the record counter
            st_data['_num_records'] += 1
        return st_data['cabecera']

    def _check_credit_card_caixabank(self, data_file):
        data_file = data_file.decode('iso-8859-1')
        try:
            credit_card_caixabank = self._parse_cc_caixabank(data_file)
        except exceptions.ValidationError:  # pragma: no cover
            return False
        return credit_card_caixabank

    def _format_date(self, date):
        # format date following user language
        lang_model = self.env['res.lang']
        lang = lang_model._lang_get(self.env.user.lang)
        date_format = lang.date_format
        return datetime.strftime(date, date_format)

    @api.model
    def _parse_file(self, data_file):
        credit_card_caixabank = self._check_credit_card_caixabank(data_file)
        if not credit_card_caixabank:  # pragma: no cover
            return super(AccountBankStatementImport, self)._parse_file(
                data_file)
        transactions = []
        for cabecera in credit_card_caixabank:
            for contratos in cabecera['contratos']:
                for tarjetas in contratos['tarjetas']:
                    monedas = {}
                    for operacion in tarjetas['operaciones']:
                        if operacion[
                                'moneda_original_operacion'] not in \
                                monedas.keys():
                            monedas[operacion[
                                'moneda_original_operacion']] = \
                                self.env['res.currency']
                    currencies = self.env['res.currency'].search(
                        [('numeric_code', 'in', list(monedas.keys()))])
                    for currency in currencies:
                        if currency.numeric_code in monedas.keys():
                            monedas[currency.numeric_code] = currency

                    for operacion in tarjetas['operaciones']:
                        conceptos = [operacion['nombre_comercio'],
                                     '( ' + operacion['localidad_comercio'] +
                                     ' )']
                        if monedas[operacion[
                            'moneda_original_operacion']].name != operacion[
                                'moneda_operacion']:
                            amount_currency = operacion['importe_origen']
                            currency_id = monedas[operacion[
                                'moneda_original_operacion']].id
                        else:
                            amount_currency = 0.0
                            currency_id = False

                        vals_line = {
                            'date': operacion['fecha_operacion'],
                            'name': ' '.join(conceptos),
                            'ref': operacion['codigo_comercio'],
                            'amount':
                                operacion['importe_operacion_moneda_contrato'],
                            'amount_currency': amount_currency,
                            'currency_id': currency_id,
                            'note': operacion,
                        }
                        transactions.append(vals_line)
        # TODO: Leer balance final segun total operaciones
        date_from = self._format_date(credit_card_caixabank[0][
            'fecha_inicio_pet_rel_op'])
        date_to = self._format_date(credit_card_caixabank[0][
            'fecha_fin_pet_rel_op'])
        periodo = '%s' % date_from + _(' to ') + '%s' % date_to
        vals_bank_statement = {
            'name': '%s' % periodo,
            'transactions': transactions,
            'balance_start': 0.0,
            'balance_end_real': 0.0,
        }
        return None, None, [vals_bank_statement]
