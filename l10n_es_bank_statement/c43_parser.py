# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import orm
from openerp.tools.translate import _
from account_statement_base_import.parser import BankStatementImportParser
from datetime import datetime

class c43_parser(BankStatementImportParser):
    """Class for defining parser for AEB C43 file format."""

    def _process_record_11(self, line):
        """11 - Registro cabecera de cuenta (obligatorio)"""
        st_group = {
            'entidad':line[2:6],
            'oficina': line[6:10],
            'cuenta': line[10:20],
            'fecha_ini': datetime.strptime(line[20:26], '%y%m%d'),
            'fecha_fin': datetime.strptime(line[26:32], '%y%m%d'),
            'divisa': line[47:50],
            'modalidad': line[50:51], # 1,2 o 3
            'nombre_propietario': line[51:77],
            'saldo_ini': float(line[33:45]) + (float(line[45:47]) / 100),
            'saldo_fin': 0,
            'num_debe': 0,
            'debe': 0,
            'num_haber': 0,
            'haber': 0,
            'lines': [],
        }
        if line[32:33] == '1':
            st_group['saldo_ini'] *= -1
        return st_group

    def _process_record_22(self, line):
        """22 - Registro principal de movimiento (obligatorio)"""
        st_line = {
            'of_origen': line[6:10],
            'fecha_operación': datetime.strptime(line[10:16], '%y%m%d'),
            'fecha_valor': datetime.strptime(line[16:22], '%y%m%d'),
            'concepto_c': line[22:24],
            'concepto_p': line[24:27],
            'importe': (float(line[28:40]) + (float(line[40:42]) / 100)),
            'num_documento': line[41:52],
            'referencia1': line[52:64].strip(),
            'referencia2': line[64:].strip(),
            'conceptos': '',
        }
        if line[27:28] == '1':
            st_line['importe'] *= -1
        return st_line

    def _process_record_23(self, st_line, line):
        """23 - Registros complementarios de concepto (opcionales y hasta un 
        máximo de 5)"""
        # Se han unido los dos conceptos line[4:42]+line[42:] en uno
        st_line['conceptos'] += line[4:].strip()
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
        st_group['debe'] += float(line[25:37]) + float(line[37:39]) / 100
        st_group['num_haber'] += int(line[39:44])
        st_group['haber'] += float(line[44:56]) + float(line[56:58]) / 100
        st_group['saldo_fin'] += float(line[59:71]) + float(line[71:73]) / 100
        if line[58:59] == '1':
            st_group['saldo_fin'] *= -1
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
            raise orm.except_orm(_('Error in C43 file'),
                _("Number of debit records doesn't match with the defined in "
                  "the last record of account."))
        if  st_group['num_haber'] != credit_count:
            raise orm.except_orm(_('Error in C43 file'),
                _("Number of credit records doesn't match with the defined "
                  "in the last record of account."))
        if abs(st_group['debe'] - debit) > 0.005:
            raise orm.except_orm(_('Error in C43 file'),
                _("Debit amount doesn't match with the defined in the last "
                  "record of account."))
        if abs(st_group['haber'] - credit) > 0.005:
            raise orm.except_orm(_('Error in C43 file'),
                _("Credit amount doesn't match with the defined in the last "
                  "record of account."))
        # Note: Only perform this check if the balance is defined on the file
        # record, as some banks may leave it empty (zero) on some circumstances
        # (like CaixaNova extracts for VISA credit cards).
        if st_group['saldo_fin']:
            balance = st_group['saldo_ini'] + credit - debit
            if abs(st_group['saldo_fin'] - balance) > 0.005:
                raise orm.except_orm(_('Error in C43 file'),
                    _("Final balance amount = (initial balance + credit "
                      "- debit) doesn't match with the defined in the last "
                      "record of account."))
        return st_group

    def _process_record_88(self, st_data, line):
        """88 - Registro de fin de archivo"""
        st_data['num_registros'] = int(line[20:26])
        # File level checks
        if st_data['num_registros'] != st_data['_num_records']:
            raise orm.except_orm(_('Error in C43 file'),
                _("Number of records doesn't match with the defined in the "
                  "last record."))
        return st_data

    @classmethod
    def parser_for(cls, parser_name):
        """
        Used by the new_bank_statement_parser class factory.
        @return: True if the providen name is 'aeb_c43'.
        """
        return parser_name == 'aeb_c43'

    def _parse(self, *args, **kwargs):
        """
        Launch the parsing itself.
        """
        # st_data will contain data read from the file
        st_data = {
            '_num_records': 0, # Number of records really counted
            'groups': [], # Info about each of the groups (account groups)
        }
        for raw_line in self.filebuffer.split("\n"):
            if not raw_line:
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
                raise orm.except_orm(_('Error in C43 file'),
                            _('Record type %s is not valid.') % raw_line[0:2])
            # Update the record counter
            st_data['_num_records'] += 1
        self.result_row_list = []
        for st_group in st_data['groups']:
            self.result_row_list += st_group['lines']
        return True

    def _validate(self, *args, **kwargs):
        """Nothing to do here."""
        return True

    def get_st_line_vals(self, line, *args, **kwargs):
        """
        This method must return a dict of vals that can be passed to create
        method of statement line in order to record it. It is the
        responsibility of every parser to give this dict of vals, so each one
        can implement his own way of recording the lines.
            :param: line: a dict of vals that represent a line of
                result_row_list
            :return: dict of values to give to the create method of statement
                line
        """
        return {
            'name': line['conceptos'].strip(),
            'date': line['fecha_operación'],
            'amount': line['importe'],
            'ref': line['referencia2'],
            'label': line['concepto_c'],
        }

    def old_reconcile_method(self, cr, uid, ids, context=None):
        st_obj = pool.get('account.bank.statement')
        st_line_obj = pool.get('account.bank.statement.line')
        concepto_obj = pool.get('l10n.es.extractos.concepto')
        reconciled_move_lines_ids = []
        for st_line in st_data['lines']:
            # Search the 'concepto' for this line
            concepto_ids = concepto_obj.search(cr, uid, [
                                ('code', '=', st_line['concepto_c']),
                                ('company_id', '=',statement.company_id.id),
                            ], context=context)
            concepto = None
            if concepto_ids:
                concepto = concepto_obj.browse(cr, uid, concepto_ids[0], context=context)
            # Basic statement line values
            values = {
                'statement_id': statement_id,
                'name': concepto and concepto.name or '-',
                'date': st_line['fecha_operación'],
                'amount': st_line['importe'],
                'ref': ' '.join([st_line['referencia1'].strip(),
                                st_line['referencia2'].strip()]),
                'note': st_line['conceptos'].strip(),
            }
            if st_line['concepto_c'] in ['03']: # Recibo/Letra domiciliado
                values['type'] = 'supplier'
            elif st_line['concepto_c'] in ['14']: # Devolución/Impagado
                values['type'] = 'customer'
            elif st_line['concepto_c'] in ['05', '06', '07', '08', '09', '10', '11', '12', '13', '15', '16', '17', '98', '99']:
                values['type'] = 'general'
            else:
                values['type'] = (st_line['importe'] >= 0 and 'customer') or 'supplier'
            # Search for lines or payment orders to reconcile against this line
            line2reconcile = None
            maturity_date = st_line['fecha_valor']
            max_date_diff = c43_wizard.reco_max_days * 3600*24
            account_id = concepto and concepto.account_id.id
            partner = None
            if values['type'] in ['customer', 'supplier']:
                # Use partner accounts
                partner = st_line_obj._find_partner_by_line_vat_number(cr, uid, st_line['referencia1'][:9], context) or \
                          st_line_obj._find_partner_by_line_vat_number(cr, uid, st_line['referencia1'][-9:], context) or \
                          st_line_obj._find_partner_by_line_vat_number(cr, uid, st_line['referencia2'][:9], context) or \
                          st_line_obj._find_partner_by_line_vat_number(cr, uid, st_line['referencia2'][-9:], context)
                if partner:
                    # Use the partner accounts
                    if values['type'] == 'customer':
                        account_id = partner.property_account_receivable and partner.property_account_receivable.id or account_id
                    else:
                        account_id = partner.property_account_payable and partner.property_account_payable.id or account_id
                else:
                    # Use the generic partner accounts
                    default_account_receivable_id, default_account_payable_id = st_line_obj._get_default_partner_account_ids(cr, uid, context)
                    if values['type'] == 'customer':
                        account_id = default_account_receivable_id or account_id
                    else:
                        account_id = default_account_payable_id or account_id
            if not account_id:
                raise osv.except_osv(_('Error'), _('A default account has not been defined for the C43 concept ') + st_line['concepto_c'] )
            values.update({
                'account_id': account_id,
                'partner_id': partner and partner.id or None,
                'voucher_id': None,
            })
            line_id = st_line_obj.create(cr, uid, values, context=context)
            # Store extra information needed to search possible move lines to reconcile
            info = {}
            for key in ('conceptos', 'referencia1', 'referencia2'):
                info[key] = st_line[key]
            pool.get('account.bank.statement.line.data').create_from_dictionary(cr, uid, line_id, info, context)
            # It's a bit slow doing this process by storing 'search_by' in the database each time
            # but simplifies the API and at the same time makes 'search_by' to be stored as the 
            # last search type. The one that found the move line to reconcile.
            found = False
            for search_by in ('reference_and_amount','vat_and_amount','amount','payment_order','rules'):
                # Check if the 'search_by' type of search should be applied.
                if not getattr(c43_wizard, 'reco_%s' % search_by):
                    continue
                pool.get('account.bank.statement.line').write(cr, uid, [line_id], {
                    'search_by': search_by,
                }, context)
                result = pool.get('account.bank.statement.line').reconcile_search(cr, uid, [line_id], context, maturity_date, max_date_diff)
                if result[line_id] or search_by == 'payment_order':
                    found = True
                    break
            if not found:
                # If no move line was found, set 'search_by' field to 'none'
                pool.get('account.bank.statement.line').write(cr, uid, [line_id], {
                    'search_by': 'none',
                }, context)
        # Update the statement
        st_obj.write(cr, uid, [statement_id], {
                                'date': st_data['fecha_fin'],
                                'balance_start': st_data['saldo_ini'],
                                'balance_end_real': st_data['saldo_fin'],
                            }, context=context)