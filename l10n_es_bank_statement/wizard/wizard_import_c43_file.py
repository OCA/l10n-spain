# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2010 Pexego Sistemas Informáticos. All Rights Reserved
#                       Borja López Soilán <borjals@pexego.es>
#    $Id$
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
    
import wizard
import pooler
import base64
import time
import re
from tools.translate import _



class wizard_import_c43_file(wizard.interface):
    """
    C43 file importation wizard for bank statements.
    """

    ############################################################################
    # Forms
    ############################################################################

    _init_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Bank statements import according to norm C43">
        <group colspan="4">
            <label string="Bank Statements File:"/>
            <newline/>
            <field name="file_name" nolabel="1"/>
            <field name="file" filename="file_name" nolabel="1"/>
        </group>
        <group colspan="4">
            <separator string="Automatic reconciliation options" colspan="4"/>
            <field name="reco_reference_and_amount" colspan="4"/>
            <field name="reco_vat_and_amount" colspan="4"/>
            <field name="reco_amount" colspan="4"/>
            <field name="reco_payment_order" colspan="4"/>
            <field name="reco_max_days" colspan="4"/>
        </group>
    </form>"""

    _init_fields = {
        'file': {
            'string': 'Bank Statements File',
            'type': 'binary',
            'required': True,
        },
        'file_name': {
            'string': 'Bank Statements File',
            'type': 'char',
            'size': 64,
            'readonly':True
        },
        'reco_reference_and_amount' : {'string': 'Reconcile by reference and amount', 'type': 'boolean'},
        'reco_vat_and_amount' : {'string': 'Reconcile by VAT number and amount', 'type': 'boolean'},
        'reco_amount' : {'string': 'Reconcile by amount', 'type': 'boolean'},
        'reco_payment_order' : {'string': 'Reconcile payment orders by total amount', 'type': 'boolean'},
        'reco_max_days' : {'string': 'Max. days from statement date', 'type': 'integer',
                    'help': 'Maximum difference in days, between the maturity date of the entry to reconcile and the bank statement entry'},
    }


    ############################################################################
    # Actions
    ############################################################################

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
            raise wizard.except_wizard(_('Error in C43 file'), _('Number of debit records does not agree with the defined in the last record of account.'))
        if  st_group['num_haber'] != st_group['_credit_count']:
            raise wizard.except_wizard(_('Error in C43 file'), _('Number of credit records does not agree with the defined in the last record of account.'))
        if abs(st_group['debe'] - st_group['_debit']) > 0.005:
            raise wizard.except_wizard(_('Error in C43 file'), _('Debit amount does not agree with the defined in the last record of account.'))
        if abs(st_group['haber'] - st_group['_credit']) > 0.005:
            raise wizard.except_wizard(_('Error in C43 file'), _('Credit amount does not agree with the defined in the last record of account.'))
        # Note: Only perform this check if the balance defined on the file record,
        #       as some banks may leave it empty (zero) on some circunstances
        #       (like CaixaNova extracts for VISA credit cards).
        if st_group['saldo_fin'] != 0.0 \
                and abs(st_group['saldo_fin'] - st_group['_balance']) > 0.005:
            raise wizard.except_wizard(_('Error in C43 file'), _('Final balance amount = (initial balance + credit - debit) does not agree with the defined in the last record of account.'))

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
            raise wizard.except_wizard(_('Error in C43 file'), _('Number of records does not agree with the defined in the last record.'))

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
                raise wizard.except_wizard(_('Error in C43 file'), _('Not valid record type.'))

        return st_data


    def _attach_file_to_statement(self, cr, uid, file_contents, statement_id, context=None):
        """
        Attachs a file to the given bank statement.
        """
        if context is None:
            context = {}
        pool = pooler.get_pool(cr.dbname)
        attachment_facade = pool.get('ir.attachment')
        
        attachment_name = _('Bank Statement')

        #
        # Remove the previous statement file attachment (if any)
        #
        ids = attachment_facade.search(cr, uid, [
                    ('res_id', '=', statement_id),
                    ('res_model', '=', 'account.bank.statement'),
                    ('name', '=', attachment_name),
                ], context=context)
        if ids:
            attachment_facade.unlink(cr, uid, ids, context)

        #
        # Create the new attachment
        #
        res = attachment_facade.create(cr, uid, {
                    'name': attachment_name,
                    'datas': file_contents,
                    'datas_fname': _('bank-statement.txt'),
                    'res_model': 'account.bank.statement',
                    'res_id': statement_id,
                }, context=context)

        return res


    def _get_default_partner_account_ids(self, cr, uid, context=None):
        """
        Returns the ids of the default receivable and payable accounts
        for partners.
        """
        if context is None:
            context = {}
        pool = pooler.get_pool(cr.dbname)

        model_fields_ids = pool.get('ir.model.fields').search(cr, uid, [
                                ('name', 'in', ['property_account_receivable', 'property_account_payable']),
                                ('model', '=', 'res.partner'),
                            ], context=context)
        property_ids = pool.get('ir.property').search(cr, uid, [
                            ('fields_id', 'in', model_fields_ids),
                            ('res_id', '=', False),
                        ], context=context)

        account_receivable_id = None
        account_payable_id = None

        for prop in pool.get('ir.property').browse(cr, uid, property_ids, context=context):
            if prop.fields_id.name == 'property_account_receivable':
                try:
                    # OpenERP 5.0 and 5.2/6.0 revno <= 2236
                    account_receivable_id = int(prop.value.split(',')[1])
                except AttributeError:
                    # OpenERP 6.0 revno >= 2236
                    account_receivable_id = prop.value_reference.id
            elif prop.fields_id.name == 'property_account_payable':
                try:
                    # OpenERP 5.0 and 5.2/6.0 revno <= 2236
                    account_payable_id = int(prop.value.split(',')[1])
                except AttributeError:
                    # OpenERP 6.0 revno >= 2236
                    account_payable_id = prop.value_reference.id

        return (account_receivable_id, account_payable_id)


    def _find_partner_by_line_vat_number(self, cr, uid, st_line, context=None):
        """
        Searchs for a partner given the vat number of the line.

        Notes:
        - Depending on the bank, the VAT number may be stored on a diferent
          field. So we will have to test if any of those fields looks like a
          spanish VAT number, and then search for a partner with that VAT.
        - Only works for spanish VAT numbers.
        """
        if context is None:
            context = {}
        pool = pooler.get_pool(cr.dbname)
        partner_facade = pool.get('res.partner')

        partner = None

        possible_vat_numbers = [
            st_line['referencia1'][:9],     # Banc Sabadell
            st_line['conceptos'][:9],       # La Caixa
            st_line['conceptos'][21:30],    # Caja Rural del Jalón
        ]
        for possible_vat_number in possible_vat_numbers:
            if partner_facade.check_vat_es(possible_vat_number):
                partner_ids = partner_facade.search(cr, uid, [
                                    ('vat', 'like', 'ES%s' % possible_vat_number),
                                    ('active', '=', True),
                                ], context=context)
                if len(partner_ids) == 1:
                    # We found a partner with that VAT number
                    partner = partner_facade.browse(cr, uid, partner_ids[0], context=context)
                    break
        return partner


    def _get_nearest_move_line(self, lines, maturity_date, max_date_diff=3600*24*30):
        """
        Find the nearest move_line to a given (maturity) date
        """
        min_diff = max_date_diff
        nearest = None
        if not maturity_date:
            maturity_date = time.time()
        maturity_date_timestamp = time.mktime(time.strptime(maturity_date, '%Y-%m-%d'))
        for line in lines:
            line_date = line.date_maturity or line.date
            if line_date:
                line_timestamp = time.mktime(time.strptime(line_date, '%Y-%m-%d'))
                diff = abs(maturity_date_timestamp-line_timestamp)
                if diff < min_diff:
                    nearest = line
                    min_diff = diff
        return nearest


    def _find_entry_to_reconcile_by_line_ref_and_amount(self, cr, uid,
            st_line, reconciled_move_lines_ids,
            maturity_date, max_date_diff, context=None):
        """
        Searchs for a non-conciled entry with the same reference and amount.
        (If more than one entry matches returns False).

        Note: The operation reference may be stored in
              Banc Sabadell => 'referencia2' or 'conceptos'
              Caja Rural del Jalón => 'conceptos'
        """
        if context is None:
            context = {}
        pool = pooler.get_pool(cr.dbname)
        move_line_facade = pool.get('account.move.line')

        possible_references = [
            st_line['conceptos'],
            st_line['referencia2'],
        ]

        for reference in possible_references:
            domain = [
                ('id', 'not in', reconciled_move_lines_ids),
                ('ref', '=', reference),
                ('reconcile_id', '=', False),
                ('reconcile_partial_id', '=', False),
                ('account_id.type', 'in', ['receivable', 'payable']),
            ]
            if st_line['importe'] >= 0:
                domain.append( ('debit', '=', '%.2f' % st_line['importe']) )
            else:
                domain.append( ('credit', '=', '%.2f' % -st_line['importe']) )

            line_ids = move_line_facade.search(cr, uid, domain, context=context)
            if line_ids:
                lines = move_line_facade.browse(cr, uid, line_ids, context)
                line = self._get_nearest_move_line(lines, maturity_date, max_date_diff)
                return line
        return None


    def _find_entry_to_reconcile_by_line_vat_number_and_amount(self, cr, uid,
            st_line, reconciled_move_lines_ids,
            maturity_date, max_date_diff, context=None):
        """
        Searchs for a non-conciled entry given the partner vat number of the line and amount.
        If more than one line is found, and one of the lines has the same
        maturity date or at least the same month, that line is returned.
        """
        if context is None:
            context = {}
        pool = pooler.get_pool(cr.dbname)
        move_line_facade = pool.get('account.move.line')

        partner = self._find_partner_by_line_vat_number(cr, uid, st_line, context)
            
        if partner:
            #
            # Find a line to reconcile from this partner
            #
            domain = [
                ('id', 'not in', reconciled_move_lines_ids),
                ('partner_id', '=', partner.id),
                ('reconcile_id', '=', False),
                ('reconcile_partial_id', '=', False),
                ('account_id.type', 'in', ['receivable', 'payable']),
            ]
            if st_line['importe'] >= 0:
                domain.append( ('debit', '=', '%.2f' % st_line['importe']) )
            else:
                domain.append( ('credit', '=', '%.2f' % -st_line['importe']) )

            line_ids = move_line_facade.search(cr, uid, domain, context=context)
            if line_ids:
                lines = move_line_facade.browse(cr, uid, line_ids, context)
                line = self._get_nearest_move_line(lines, maturity_date, max_date_diff)
                return line
        return None


    def _find_entry_to_reconcile_by_line_amount(self, cr, uid,
            st_line, reconciled_move_lines_ids,
            maturity_date, max_date_diff, context=None):
        """
        Searchs for a non-conciled entry given the line amount.
        """
        if context is None:
            context = {}
        pool = pooler.get_pool(cr.dbname)
        move_line_facade = pool.get('account.move.line')

        domain = [
            ('id', 'not in', reconciled_move_lines_ids),
            ('reconcile_id', '=', False),
            ('reconcile_partial_id', '=', False),
            ('account_id.type', 'in', ['receivable', 'payable']),
        ]
        if st_line['importe'] >= 0:
            domain.append( ('debit', '=', '%.2f' % st_line['importe']) )
        else:
            domain.append( ('credit', '=', '%.2f' % -st_line['importe']) )

        line_ids = move_line_facade.search(cr, uid, domain, context=context)
        if line_ids:
            lines = move_line_facade.browse(cr, uid, line_ids, context)
            line = self._get_nearest_move_line(lines, maturity_date, max_date_diff)
            return line
        return None


    def _find_payment_order_to_reconcile_by_line_amount(self, cr, uid,
            st_line, reconciled_move_lines_ids,
            maturity_date, max_date_diff, context=None):
        """
        Searchs for a non-conciled payment order with the same total amount.
        (If more than one order matches None is returned).
        """
        if context is None:
            context = {}
        pool = pooler.get_pool(cr.dbname)

        # We require account_payment to be instaled
        if not 'payment.order' in pool.obj_list():
            return None

        #
        # The total field of the payment orders is a functional field,
        # so we can't use it for searching.
        # Also, browsing all the payment orders would be slow and not scale
        # well. So we just let Postgres do the job.
        #
        # The query will search for orders of the given amount and without
        # reconciled (or partial reconciled) lines
        #
        query = """
                SELECT payment_line.order_id, SUM(payment_line.amount_currency) AS total
                FROM payment_line
                INNER JOIN account_move_line ON (payment_line.move_line_id = account_move_line.id)
                GROUP BY payment_line.order_id
                HAVING SUM(payment_line.amount_currency) = %.2f
                        AND COUNT(account_move_line.reconcile_id) = 0
                        AND COUNT(account_move_line.reconcile_partial_id) = 0
                """
        cr.execute(query % -st_line['importe'])
        res = cr.fetchall()

        if len(res) == 1:
            # Only one payment order found, return it
            payment_order = pool.get('payment.order').browse(cr, uid, res[0][0], context)
            return payment_order
        else:
            # More than one payment order found, we return false
            return None


    #
    # Main action --------------------------------------------------------------
    #
    def _import_action(self, cr, uid, data, context=None):
        """
        Imports the C43 file selected by the user on the wizard form,
        into the current bank statement statement.
        """
        if context is None:
            context = {}
        pool = pooler.get_pool(cr.dbname)

        statement_facade = pool.get('account.bank.statement')
        statement_line_facade = pool.get('account.bank.statement.line')
        st_reconcile_facade = pool.get('account.bank.statement.reconcile')
        concepto_facade = pool.get('l10n.es.extractos.concepto')
        
        statement_id = data['id']

        statement = statement_facade.browse(cr, uid, statement_id)
        if statement.state == 'confirm':
            raise wizard.except_wizard(_('Error'), _('The bank statement is alredy confirmed. It can not be imported from file.'))


        # Load the file data into the st_data dictionary
        st_data = self._load_c43_file(cr, uid, data['form']['file'], context=context)

        #
        # Process each movement line from the statement data
        #
        reconciled_move_lines_ids = []
        for st_line in st_data['lines']:
            #
            # Search the 'concepto' for this line
            #
            concepto_ids = concepto_facade.search(cr, uid, [
                                ('code', '=', st_line['concepto_c'])
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
            order2reconcile = None

            maturity_date = st_line['fecha_valor']
            max_date_diff = data['form']['reco_max_days'] * 3600*24
            
            # Search unconciled entries by line reference and amount.
            if not line2reconcile and data['form']['reco_reference_and_amount']:
                line2reconcile = self._find_entry_to_reconcile_by_line_ref_and_amount(cr, uid,
                            st_line,
                            reconciled_move_lines_ids,
                            maturity_date,
                            max_date_diff,
                            context=context)

            # Search unconciled entries by line VAT number and amount.
            if not line2reconcile and data['form']['reco_vat_and_amount']:
                line2reconcile = self._find_entry_to_reconcile_by_line_vat_number_and_amount(cr, uid,
                            st_line,
                            reconciled_move_lines_ids,
                            maturity_date,
                            max_date_diff,
                            context=context)

            # Search unconciled entries by line amount.
            if not line2reconcile and data['form']['reco_amount']:
                line2reconcile = self._find_entry_to_reconcile_by_line_amount(cr, uid,
                            st_line,
                            reconciled_move_lines_ids,
                            maturity_date,
                            max_date_diff,
                            context=context)

            # Search unreconciled payment orders by amount.
            if not line2reconcile and data['form']['reco_payment_order'] and 'payment.order' in pool.obj_list():
                order2reconcile = self._find_payment_order_to_reconcile_by_line_amount(cr, uid,
                            st_line,
                            reconciled_move_lines_ids,
                            maturity_date,
                            max_date_diff,
                            context=context)

            #
            # Create the statement lines
            #
            if line2reconcile:
                #
                # Add a statement line reconciled against the line2reconcile
                #
                reconciled_move_lines_ids.append(line2reconcile.id)
                st_reconcile_id = st_reconcile_facade.create(cr, uid, {
                                'line_ids': [(6, 0, [line2reconcile.id])],
                            }, context=context)
                values.update({
                    'account_id': line2reconcile.account_id.id,
                    'partner_id': line2reconcile.partner_id and line2reconcile.partner_id.id or None,
                    'reconcile_id': st_reconcile_id,
                })
                statement_line_facade.create(cr, uid, values, context=context)
            elif order2reconcile:
                #
                # Add *several* statement lines reconciled against each of
                # the payment order lines.
                #
                for line in order2reconcile.line_ids:
                    reconciled_move_lines_ids.append(line.id)
                    st_reconcile_id = st_reconcile_facade.create(cr, uid, {
                                    'line_ids': [(6, 0, [line.move_line_id.id])],
                                }, context=context)
                    values.update({
                        'account_id': line.move_line_id.account_id.id,
                        'partner_id': line.move_line_id.partner_id and line.move_line_id.partner_id.id or None,
                        'reconcile_id': st_reconcile_id,
                        'amount': -line.amount_currency,
                    })
                    statement_line_facade.create(cr, uid, values, context=context)
            else:
                #
                # Add a non-reconciled statement line
                #
                account_id = concepto and concepto.account_id.id
                partner = None

                if values['type'] in ['customer', 'supplier']:
                    #
                    # Use partner accounts
                    #
                    partner = self._find_partner_by_line_vat_number(cr, uid, st_line, context)
                    if partner:
                        # Use the partner accounts
                        if values['type'] == 'customer':
                            account_id = partner.property_account_receivable and partner.property_account_receivable.id
                        else:
                            account_id = partner.property_account_payable and partner.property_account_payable.id
                    else:
                        # Use the generic partner accounts
                        default_account_receivable_id, default_account_payable_id = self._get_default_partner_account_ids(cr, uid, context)
                        if values['type'] == 'customer':
                            account_id = default_account_receivable_id
                        else:
                            account_id = default_account_payable_id
            
                if not account_id:
                    raise wizard.except_wizard(_('Error'), _('A default account has not been defined for the C43 concept ') + st_line['concepto_c'] )

                values.update({
                    'account_id': account_id,
                    'partner_id': partner and partner.id or None,
                    'reconcile_id': None,
                })
                statement_line_facade.create(cr, uid, values, context=context)


        #
        # Update the statement
        #
        statement_facade.write(cr, uid, [statement_id], {
                                'date': st_data['fecha_fin'],
                                'balance_start': st_data['saldo_ini'],
                                'balance_end_real': st_data['saldo_fin'],
                            }, context=context)

        # Attach the C43 file to the current statement
        self._attach_file_to_statement(cr, uid, data['form']['file'], statement_id)

        return {}


    ############################################################################
    # States
    ############################################################################

    states = {
        'init': {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': _init_form,
                'fields': _init_fields,
                'state': [
                    ('end', 'Cancel', 'gtk-cancel'),
                    ('import', 'Import', 'gtk-ok', True),
                ],
            },
        },
        'import': {
            'actions': [],
            'result': {
                'type': 'action',
                'action': _import_action,
                'state': 'end',
            },
        },
    }

wizard_import_c43_file('l10n_es_bank_statement.importar')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
