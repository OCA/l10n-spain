# -*- coding: utf-8 -*-
# © 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
from datetime import datetime

account_concept_mapping = {
    '01': '4300%00',
    '02': '4100%00',
    '03': '4100%00',
    '04': '4300%00',
    '05': '6800%00',
    '06': '4010%00',
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

    def _process_record_11(self, line):
        """11 - Registro cabecera de cuenta (obligatorio)"""
        st_group = {
            'entidad': line[2:6],
            'oficina': line[6:10],
            'cuenta': line[10:20],
            'fecha_ini': datetime.strptime(line[20:26], '%y%m%d'),
            'fecha_fin': datetime.strptime(line[26:32], '%y%m%d'),
            'divisa': line[47:50],
            'modalidad': line[50:51],  # 1, 2 o 3
            'nombre_propietario': line[51:77],
            'saldo_ini': float("%s.%s" % (line[33:45], line[45:47])),
            'saldo_fin': 0,
            'num_debe': 0,
            'debe': 0,
            'num_haber': 0,
            'haber': 0,
            'lines': [],
        }
        if line[32:33] == '1':
            st_group['saldo_ini'] *= -1
        self.balance_start = st_group['saldo_ini']
        return st_group

    def _process_record_22(self, line):
        """22 - Registro principal de movimiento (obligatorio)"""
        st_line = {
            'of_origen': line[6:10],
            'fecha_oper': datetime.strptime(line[10:16], '%y%m%d'),
            'fecha_valor': datetime.strptime(line[16:22], '%y%m%d'),
            'concepto_c': line[22:24],
            'concepto_p': line[24:27],
            'importe': (float(line[28:40]) + (float(line[40:42]) / 100)),
            'num_documento': line[41:52],
            'referencia1': line[52:64].strip(),
            'referencia2': line[64:].strip(),
            'conceptos': {},
        }
        if line[27:28] == '1':
            st_line['importe'] *= -1
        return st_line

    def _process_record_23(self, st_line, line):
        """23 - Registros complementarios de concepto (opcionales y hasta un
        máximo de 5)"""
        if not st_line.get('conceptos'):
            st_line['conceptos'] = {}
        st_line['conceptos'][line[2:4]] = (line[4:39].strip(),
                                           line[39:].strip())
        return st_line

    def _process_record_24(self, st_line, line):
        """24 - Registro complementario de información de equivalencia del
        importe (opcional y sin valor contable)"""
        st_line['divisa_eq'] = line[4:7]
        st_line['importe_eq'] = float(line[7:19]) + (float(line[19:21]) / 100)
        return st_line

    def _process_record_33(self, st_group, line):
        """33 - Registro final de cuenta"""
        st_group['num_debe'] += int(line[20:25])
        st_group['debe'] += float("%s.%s" % (line[25:37], line[37:39]))
        st_group['num_haber'] += int(line[39:44])
        st_group['haber'] += float("%s.%s" % (line[44:56], line[56:58]))
        st_group['saldo_fin'] += float("%s.%s" % (line[59:71], line[71:73]))
        if line[58:59] == '1':
            st_group['saldo_fin'] *= -1
        self.balance_end = st_group['saldo_fin']
        # Group level checks
        debit_count = 0
        debit = 0.0
        credit_count = 0
        credit = 0.0
        for st_line in st_group['lines']:
            if st_line['importe'] < 0:
                debit_count += 1
                debit -= st_line['importe']
            else:
                credit_count += 1
                credit += st_line['importe']
        if st_group['num_debe'] != debit_count:
            raise exceptions.Warning(
                _("Number of debit records doesn't match with the defined in "
                  "the last record of account."))
        if st_group['num_haber'] != credit_count:
            raise exceptions.Warning(
                _('Error in C43 file'),
                _("Number of credit records doesn't match with the defined "
                  "in the last record of account."))
        if abs(st_group['debe'] - debit) > 0.005:
            raise exceptions.Warning(
                _('Error in C43 file'),
                _("Debit amount doesn't match with the defined in the last "
                  "record of account."))
        if abs(st_group['haber'] - credit) > 0.005:
            raise exceptions.Warning(
                _("Credit amount doesn't match with the defined in the last "
                  "record of account."))
        # Note: Only perform this check if the balance is defined on the file
        # record, as some banks may leave it empty (zero) on some circumstances
        # (like CaixaNova extracts for VISA credit cards).
        if st_group['saldo_fin'] and st_group['saldo_ini']:
            balance = st_group['saldo_ini'] + credit - debit
            if abs(st_group['saldo_fin'] - balance) > 0.005:
                raise exceptions.Warning(
                    _("Final balance amount = (initial balance + credit "
                      "- debit) doesn't match with the defined in the last "
                      "record of account."))
        return st_group

    def _process_record_88(self, st_data, line):
        """88 - Registro de fin de archivo"""
        st_data['num_registros'] = int(line[20:26])
        # File level checks
        # Some banks (like Liderbank) are informing this record number
        # including the record 88, so checking this with the absolute
        # difference allows to bypass the error
        if abs(st_data['num_registros'] - st_data['_num_records']) > 1:
            raise exceptions.Warning(
                _("Number of records doesn't match with the defined in the "
                  "last record."))
        return st_data

    def _parse(self, data_file):
        # st_data will contain data read from the file
        st_data = {
            '_num_records': 0,  # Number of records really counted
            'groups': [],  # Info about each of the groups (account groups)
        }
        for raw_line in data_file.split("\n"):
            if not raw_line.strip():
                continue
            code = raw_line[0:2]
            if code == '11':
                st_group = self._process_record_11(raw_line)
                st_data['groups'].append(st_group)
            elif code == '22':
                st_line = self._process_record_22(raw_line)
                st_group['lines'].append(st_line)
            elif code == '23':
                self._process_record_23(st_line, raw_line)
            elif code == '24':
                self._process_record_24(st_line, raw_line)
            elif code == '33':
                self._process_record_33(st_group, raw_line)
            elif code == '88':
                self._process_record_88(st_data, raw_line)
            elif ord(raw_line[0]) == 26:
                # CTRL-Z (^Z), is often used as an end-of-file marker in DOS
                continue
            else:
                raise exceptions.ValidationError(
                    _('Record type %s is not valid.') % raw_line[0:2])
            # Update the record counter
            st_data['_num_records'] += 1
        return st_data['groups']

    def _check_n43(self, data_file):
        data_file = data_file.decode('iso-8859-1')
        try:
            n43 = self._parse(data_file)
        except exceptions.ValidationError:
            return False
        return n43

    def _get_ref(self, line):
        try:
            ref1 = int(line['referencia1'])
        except:
            ref1 = line['referencia1']
        try:
            ref2 = int(line['referencia2'])
        except:
            ref2 = line['referencia2']
        if not ref1:
            return line['referencia2'] or '/'
        elif not ref2:
            return line['referencia1'] or '/'
        else:
            return "%s / %s" % (line['referencia1'], line['referencia2'])

    def _get_partner_from_caixabank(self, conceptos):
        partner_obj = self.env['res.partner']
        partner = partner_obj.browse()
        # Try to match from VAT included in concept complementary record #02
        if conceptos.get('02'):
            vat = conceptos['02'][0][:2] + conceptos['02'][0][7:]
            if vat:
                partner = partner_obj.search([('vat', '=', vat)], limit=1)
        if not partner:
            # Try to match from partner name
            if conceptos.get('01'):
                name = conceptos['01'][0][4:] + conceptos['01'][1]
                if name:
                    partner = partner_obj.search(
                        [('name', 'ilike', name)], limit=1)
        return partner

    def _get_partner_from_santander(self, conceptos):
        partner_obj = self.env['res.partner']
        partner = partner_obj.browse()
        # Try to match from VAT included in concept complementary record #01
        if conceptos.get('01'):
            if conceptos['01'][1]:
                vat = conceptos['01'][1]
                if vat:
                    partner = partner_obj.search(
                        [('vat', 'ilike', vat)], limit=1)
        if not partner:
            # Try to match from partner name
            if conceptos.get('01'):
                name = conceptos['01'][0]
                if name:
                    partner = partner_obj.search(
                        [('name', 'ilike', name)], limit=1)
        return partner

    def _get_partner_from_bankia(self, conceptos):
        partner_obj = self.env['res.partner']
        partner = partner_obj.browse()
        # Try to match from partner name
        if conceptos.get('01'):
            vat = conceptos['01'][0][:2] + conceptos['01'][0][7:]
            if vat:
                partner = partner_obj.search([('vat', '=', vat)], limit=1)
        return partner

    def _get_partner_from_sabadell(self, conceptos):
        partner_obj = self.env['res.partner']
        partner = partner_obj.browse()
        # Try to match from partner name
        if conceptos.get('01'):
            name = conceptos['01'][1]
            if name:
                partner = partner_obj.search(
                    [('name', 'ilike', name)], limit=1)
        return partner

    def _get_partner(self, line):
        if not line.get('conceptos'):
            return self.env['res.partner']
        partner = self._get_partner_from_caixabank(line['conceptos'])
        if not partner:
            partner = self._get_partner_from_santander(line['conceptos'])
        if not partner:
            partner = self._get_partner_from_bankia(line['conceptos'])
        if not partner:
            partner = self._get_partner_from_sabadell(line['conceptos'])
        return partner

    def _get_account(self, line):
        accounts = []
        if line['concepto_c']:
            accounts = self.env['account.account'].search(
                [('code', 'like',
                  account_concept_mapping[line['concepto_c']])])
        return accounts and accounts[0].id or False

    @api.model
    def _parse_file(self, data_file):
        n43 = self._check_n43(data_file)
        if not n43:
            return super(AccountBankStatementImport, self)._parse_file(
                data_file)
        transactions = []
        for group in n43:
            for line in group['lines']:
                conceptos = []
                for concept_line in line['conceptos']:
                    conceptos.extend(x.strip()
                                     for x in line['conceptos'][concept_line]
                                     if x.strip())
                vals_line = {
                    'date': fields.Date.to_string(
                        line[self.journal_id.n43_date_type]),
                    'name': ' '.join(conceptos),
                    'ref': self._get_ref(line),
                    'amount': line['importe'],
                    'note': line,
                }
                c = line['conceptos']
                if c.get('01'):
                    vals_line['partner_name'] = c['01'][0] + c['01'][1]
                if not vals_line['name']:
                    vals_line['name'] = vals_line['ref']
                transactions.append(vals_line)
        vals_bank_statement = {
            'transactions': transactions,
            'balance_start': n43 and n43[0]['saldo_ini'] or 0.0,
            'balance_end_real': n43 and n43[-1]['saldo_fin'] or 0.0,
        }
        str_currency = self.journal_id.currency and \
            self.journal_id.currency.name or \
            self.journal_id.company_id.currency_id.name
        return str_currency, False, [vals_bank_statement]

    @api.model
    def _get_hide_journal_field(self):
        # Show the journal_id field if not coming from a context where is set
        return bool(self.env.context.get('journal_id'))

    def _complete_statement(self, stmt_vals, journal_id, account_number):
        """Match partner_id if if hasn't been deducted yet."""
        res = super(AccountBankStatementImport, self)._complete_statement(
            stmt_vals, journal_id, account_number)
        for line_vals in res['transactions']:
            if not line_vals['partner_id'] and line_vals.get('note'):
                line_vals['partner_id'] = self._get_partner(
                    line_vals['note']).id
        return res
