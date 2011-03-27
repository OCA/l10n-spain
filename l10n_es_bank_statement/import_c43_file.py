# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2010 Pexego Sistemas Informáticos. All Rights Reserved
#                       Borja López Soilán <borjals@pexego.es>
#                       Alberto Luengo Cabanillas <alberto@pexego.es>
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""
C43 file importation wizard for bank statements.
"""
from osv import fields,osv
import wizard
import pooler
import base64
import time
import re
from tools.translate import _

class l10n_es_bank_statement_import_c43_wizard(osv.osv_memory):
    """
    C43 file importation wizard for bank statements.
    """

    def _process_record_11(self, cr, uid, st_data, line, context):
        """
        11 - Registro cabecera de cuenta (obligatorio)
        """
        #
        # Add a new group to the statement groups
        #
        st_group = {}
        st_data['groups'] = st_data.get('groups', [])
        st_data['groups'].append(st_group)

        #
        # Set the group values
        #
        st_group.update({
            'entidad':line[2:6],
            'oficina': line[6:10],
            'cuenta': line[10:20],
            'fecha_ini': time.strftime('%Y-%m-%d', time.strptime(line[20:26], '%y%m%d')),
            'fecha_fin': time.strftime('%Y-%m-%d', time.strptime(line[26:32], '%y%m%d')),
            'divisa': line[47:50],
            'modalidad': line[50:51], # 1,2 o 3
            'nombre_propietario': line[51:77], # Nombre abreviado propietario cuenta
            'saldo_ini': (float(line[33:45]) + (float(line[45:47]) / 100)) * (line[32:33] == '1' and -1 or 1),
            'saldo_fin': 0,
            'num_debe': 0,
            'debe': 0,
            'num_haber': 0,
            'haber': 0,
            '_debit_count': 0,
            '_debit': 0,
            '_credit_count': 0,
            '_credit': 0,
            '_balance': 0,
        })

        #
        # Use the first group initial balance and date, as initial
        #   balance and date for the full statement.
        #
        if st_data.get('saldo_ini', None) is None:
            st_data['saldo_ini'] = st_group['saldo_ini']
            st_data['fecha_ini'] = st_group['fecha_ini']

        # Update the record counter
        st_data['_num_records'] = st_data.get('_num_records', 0) + 1

        return st_group


    def _process_record_22(self, cr, uid, st_data, line, context):
        """
        22 - Registro principal de movimiento (obligatorio)
        """

        #
        # Add a new line to the statement lines
        #
        st_line = {}
        st_data['lines'] = st_data.get('lines', [])
        st_data['lines'].append(st_line)

        #
        # Set the line values
        #
        st_line.update({
            'of_origen': line[6:10],
            'fecha_opera': time.strftime('%Y-%m-%d', time.strptime(line[10:16], '%y%m%d')),
            'fecha_valor': time.strftime('%Y-%m-%d', time.strptime(line[16:22], '%y%m%d')),
            'concepto_c': line[22:24],
            'concepto_p': line[24:27],
            'importe': (float(line[28:40]) + (float(line[40:42]) / 100)) * (line[27:28] == '1' and -1 or 1),
            'num_documento': line[41:52],
            'referencia1': line[52:64],
            'referencia2': line[64:],
            'conceptos': '',
        })

        #
        # Update the (last) group totals
        #
        st_group = st_data['groups'][-1]
        if st_line['importe'] < 0:
            st_group['_debit_count'] += 1
            st_group['_debit'] -= st_line['importe']
        else:
            st_group['_credit_count'] += 1
            st_group['_credit'] += st_line['importe']

        # Update the record counter
        st_data['_num_records'] += 1

        return st_line


    def _process_record_23(self, cr, uid, st_data, line, context):
        """
        23 - Registros complementarios de concepto (opcionales y hasta un máximo de 5)
        """
        #
        # Update the current (last) line
        #
        st_line = st_data['lines'][-1]
        st_line['conceptos'] += line[4:] # Se han unido los dos conceptos line[4:42]+line[42:] en uno

        # Update the record counter
        st_data['_num_records'] += 1

        return st_line


    def _process_record_24(self, cr, uid, st_data, line, context):
        """
        24 - Registro complementario de información de equivalencia del importe (opcional y sin valor contable)
        """
        #
        # Update the current (last) line
        #
        st_line = st_data['lines'][-1]
        st_line['divisa_eq'] = line[4:7]
        st_line['importe_eq'] = float(line[7:19]) + (float(line[19:21]) / 100)

        # Update the record counter
        st_data['_num_records'] += 1

        return st_line


    def _process_record_33(self, cr, uid, st_data, line, context):
        """
        33 -  Registro final de cuenta
        """
        #
        # Update the (last) group
        #
        st_group = st_data['groups'][-1]
        st_group.update({
            'num_debe': st_group['num_debe'] + int(line[20:25]),
            'debe': st_group['debe'] + float(line[25:37]) + (float(line[37:39]) / 100),
            'num_haber': st_group['num_haber'] + int(line[39:44]),
            'haber': st_group['haber'] + float(line[44:56]) + (float(line[56:58]) / 100),
            'saldo_fin': st_group['saldo_fin'] + (float(line[59:71]) + (float(line[71:73]) / 100)) * (line[58:59] == '1' and -1 or 1),
            '_balance': st_group['saldo_ini'] + st_group['_credit'] - st_group['_debit']
        })

        # Update the record counter
        st_data['_num_records'] += 1

        #
        # Group level checks
        #
        if st_group['num_debe'] != st_group['_debit_count']:
            raise osv.except_osv(_('Error in C43 file'), _('Number of debit records does not agree with the defined in the last record of account.'))
        if  st_group['num_haber'] != st_group['_credit_count']:
            raise osv.except_osv(_('Error in C43 file'), _('Number of credit records does not agree with the defined in the last record of account.'))
        if abs(st_group['debe'] - st_group['_debit']) > 0.005:
            raise osv.except_osv(_('Error in C43 file'), _('Debit amount does not agree with the defined in the last record of account.'))
        if abs(st_group['haber'] - st_group['_credit']) > 0.005:
            raise osv.except_osv(_('Error in C43 file'), _('Credit amount does not agree with the defined in the last record of account.'))
        # Note: Only perform this check if the balance defined on the file record,
        #       as some banks may leave it empty (zero) on some circunstances
        #       (like CaixaNova extracts for VISA credit cards).
        if st_group['saldo_fin'] != 0.0 \
                and abs(st_group['saldo_fin'] - st_group['_balance']) > 0.005:
            raise osv.except_osv(_('Error in C43 file'), _('Final balance amount = (initial balance + credit - debit) does not agree with the defined in the last record of account.'))

        return st_group


    def _process_record_88(self, cr, uid, st_data, line, context):
        """
        88 - Registro de fin de archivo
        """
        # We will use the last group final balance and date, as final
        #   balance and date for the full statement.
        st_group = st_data['groups'][-1]

        # Update the statement
        st_data.update({
            'num_registros': int(line[20:26]),
            'fecha_fin': st_group['fecha_fin'],
            'saldo_fin': st_group['saldo_fin'],
        })

        #
        # File level checks
        #
        if st_data['num_registros'] != st_data['_num_records']:
            raise osv.except_osv(_('Error in C43 file'), _('Number of records does not agree with the defined in the last record.'))

        return st_data


    def _load_c43_file(self, cr, uid, file_contents, context=None):
        """
        Reads a c43 file and returns a dictionary containing the file data:

            _num_records:   Number of records really counted
            num_registros:  Number of records declared on the file
            fecha_fin:      Final date (as the last record group)
            saldo_fin:      Final balance (from the last record group)
            groups:         Info about each of the groups (account groups):
                _debit_count
                _debit
                _credit_count
                _credit
                entidad
                oficina
                cuenta
                fecha_ini
                fecha_fin
                saldo_ini
                saldo_fin
                divisa
                modalidad
                nombre_propietario
            lines:          Info about each of the moves
                of_origen
                fecha_opera
                fecha_valor
                concepto_c
                concepto_p
                importe
                num_documento
                referencia1
                referencia2
                conceptos
                divisa_eq
                importe_eq
        """
        if context is None:
            context = {}

        #
        # st_data will contain the data read from the file, plus the internal
        # counters used for checking.
        #
        st_data = {
            '_num_records': 0,      # Number of records really counted
            'num_registros': 0,     # Number of records declared on the file
            'fecha_fin': None,      # Final date (as the last record group)
            'saldo_fin': None,      # Final balance (from the last record group)
            'groups': [],           # Info about each of the groups (account groups)
            'lines': [],            # Info about each of the moves
        }

        #
        # Read the C43 file
        #
        decoded_file_contents = base64.decodestring(file_contents)
        try:
            unicode(decoded_file_contents, 'utf8')
        except Exception, ex: # Si no puede convertir a UTF-8 es que debe estar en ISO-8859-1: Lo convertimos
            decoded_file_contents = unicode(decoded_file_contents, 'iso-8859-1').encode('utf-8')

        #
        # Process the file lines
        #
        for line in decoded_file_contents.split("\n"):
            if len(line) == 0:
                continue
            if line[0:2] == '11': # Registro cabecera de cuenta (obligatorio)
                self._process_record_11(cr, uid, st_data, line, context)
            elif line[0:2] == '22': # Registro principal de movimiento (obligatorio)
                self._process_record_22(cr, uid, st_data, line, context)
            elif line[0:2] == '23': # Registros complementarios de concepto (opcionales y hasta un máximo de 5)
                self._process_record_23(cr, uid, st_data, line, context)
            elif line[0:2] == '24': # Registro complementario de información de equivalencia del importe (opcional y sin valor contable)
                self._process_record_24(cr, uid, st_data, line, context)
            elif line[0:2] == '33': # Registro final de cuenta
                self._process_record_33(cr, uid, st_data, line, context)
            elif line[0:2] == '88': # Registro de fin de archivo
                self._process_record_88(cr, uid, st_data, line, context)
            elif ord(line[0]) == 26: # CTRL-Z (^Z), is often used as an end-of-file marker in DOS
                pass
            else:
                raise osv.except_osv(_('Error in C43 file'), _('Record type %s is not valid.') % line[0:2])

        return st_data

    #
    # Main action --------------------------------------------------------------
    #
    def import_action(self, cr, uid, ids, context=None):
        """
        Imports the C43 file selected by the user on the wizard form,
        into the current bank statement statement.
        """
        if context is None:
            context = {}

        pool = pooler.get_pool(cr.dbname)
        statement_facade = pool.get('account.bank.statement')
        statement_line_facade = pool.get('account.bank.statement.line')
        concepto_facade = pool.get('l10n.es.extractos.concepto')

        for c43_wizard in self.browse(cr,uid,ids,context):
            statement_id = context['active_id']

            statement = statement_facade.browse(cr, uid, statement_id)
            if statement.state == 'confirm':
                raise osv.except_osv(_('Error!'), _('The bank statement is alredy confirmed. It can not be imported from file.'))

            # Load the file data into the st_data dictionary
            st_data = self._load_c43_file(cr, uid, c43_wizard.file, context=context)

            #
            # Process each movement line from the statement data
            #
            reconciled_move_lines_ids = []
            for st_line in st_data['lines']:
                #
                # Search the 'concepto' for this line
                #
                concepto_ids = concepto_facade.search(cr, uid, [
                                    ('code', '=', st_line['concepto_c']),
                                    ('company_id', '=',statement.company_id.id),
                                ], context=context)
                concepto = None
                if concepto_ids:
                    concepto = concepto_facade.browse(cr, uid, concepto_ids[0], context=context)

                #
                # Basic statement line values
                #
                note = st_line['conceptos'].strip()
                ref = re.sub(' +', ' ', note).strip()
                values = {
                    'statement_id': statement_id,
                    'name': concepto and concepto.name or '-',
                    'date': st_line['fecha_opera'],
                    'amount': st_line['importe'],
                    'ref': ref,
                    'note': note,
                }

                if st_line['concepto_c'] in ['03']: # Recibo/Letra domiciliado
                    values['type'] = 'supplier'
                elif st_line['concepto_c'] in ['14']: # Devolución/Impagado
                    values['type'] = 'customer'
                elif st_line['concepto_c'] in ['05', '06', '07', '08', '09', '10', '11', '12', '13', '15', '16', '17', '98', '99']:
                    values['type'] = 'general'
                else:
                    values['type'] = (st_line['importe'] >= 0 and 'customer') or 'supplier'

                #
                # Search for lines or payment orders to reconcile against this line
                #
                line2reconcile = None

                maturity_date = st_line['fecha_valor']
                max_date_diff = c43_wizard.reco_max_days * 3600*24

                account_id = concepto and concepto.account_id.id
                partner = None

                if values['type'] in ['customer', 'supplier']:
                    #
                    # Use partner accounts
                    #
                    partner = statement_line_facade._find_partner_by_line_vat_number(cr, uid, st_line, context)
                    if partner:
                        # Use the partner accounts
                        if values['type'] == 'customer':
                            account_id = partner.property_account_receivable and partner.property_account_receivable.id or account_id
                        else:
                            account_id = partner.property_account_payable and partner.property_account_payable.id or account_id
                    else:
                        # Use the generic partner accounts
                        default_account_receivable_id, default_account_payable_id = statement_line_facade._get_default_partner_account_ids(cr, uid, context)
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

                line_id = statement_line_facade.create(cr, uid, values, context=context)

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
                    if result[line_id]:
                        found = True
                        break

                if not found:
                    # If no move line was found, set 'search_by' field to 'none'
                    pool.get('account.bank.statement.line').write(cr, uid, [line_id], {
                        'search_by': 'none',
                    }, context)


            #
            # Update the statement
            #
            statement_facade.write(cr, uid, [statement_id], {
                                    'date': st_data['fecha_fin'],
                                    'balance_start': st_data['saldo_ini'],
                                    'balance_end_real': st_data['saldo_fin'],
                                }, context=context)

            # Attach the C43 file to the current statement
            data = base64.encodestring( c43_wizard.file )
            res = statement_facade._attach_file_to_statement(cr, uid, data, statement_id, _('Bank Statement'), _('bank-statement.txt') )

        return {}


    _name = 'l10n.es.bank.statement.import.c43.wizard'

    _columns = {
        'file': fields.binary('Bank Statements File', required=True, filename='file_name'),
        'file_name': fields.char('Bank Statements File', size=64, readonly=True),
        'reco_reference_and_amount': fields.boolean('Reconcile by reference and amount'),
        'reco_vat_and_amount' : fields.boolean('Reconcile by VAT number and amount'),
        'reco_amount' : fields.boolean('Reconcile by amount'),
        'reco_rules' : fields.boolean('Statement Line Rules'),
        'reco_payment_order': fields.boolean('Reconcile payment orders by total amount'),
        'reco_max_days' : fields.integer('Max. days from statement date',help='Maximum difference in days, between the maturity date of the entry to reconcile and the bank statement entry')
        }

l10n_es_bank_statement_import_c43_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
