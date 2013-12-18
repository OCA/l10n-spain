# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP - Import operations model 347 engine
#    Copyright (C) 2009 Asr Oss. All Rights Reserved
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
Create FYC entries wizards
"""
__author__ = """Borja López Soilán (Pexego) - borjals@pexego.es"""

from tools.translate import _
import wizard
import pooler
import time
import threading
import sql_db
import netsvc
from tools import config

class wizard_run(wizard.interface):
    """
    Wizard to create the FYC entries.
    """

    ############################################################################
    # Forms
    ############################################################################

    _init_run_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Fiscal Year Closing" colspan="4" width="400">
        <label string="This wizard will perform the selected operations." colspan="4"/>
        <label string="" colspan="4"/>
        <label string="It will create account moves for the operations you selected, skipping those already created." colspan="4"/>
        <label string="Non-selected operations will be canceled." colspan="4"/>
    </form>"""

    _init_cancel_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Fiscal Year Closing" colspan="4" width="400">
        <label string="This wizard will cancel the selected operations." colspan="4"/>
        <label string="" colspan="4"/>
        <label string="It will remove the previously generated account moves." colspan="4"/>
        <label string="Closed periods, and the fiscal year, will be reopened." colspan="4"/>
    </form>"""

    _progress_form = '''<?xml version="1.0"?>
    <form string="Fiscal Year Closing - Working" colspan="4" width="400">
        <label string="The process may take a while." colspan="4"/>
        <label string="" colspan="4"/>
        <field name="task_progress" widget="progressbar" colspan="4"/>
        <field name="progress" widget="progressbar" colspan="4"/>
    </form>'''

    _progress_fields = {
        'task_progress': { 'string': 'Task Progress', 'type':'float' },
        'progress': { 'string': 'Total Progress', 'type':'float' },
    }


    _done_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Fiscal Year Closing - Done" colspan="4" width="400">
        <label string="The selected operations have been performed sucessfuly." colspan="4"/>
        <label string="" colspan="4"/>
    </form>"""

    _show_exception_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Fiscal Year Closing - Error!" colspan="4" width="400">
        <label string="Error: One of the selected operations has failed!" colspan="4"/>
        <label string="" colspan="4"/>
        <separator string="Details"/>
        <field name="exception_text" colspan="4" nolabel="1"/>
    </form>"""

    _show_exception_fields = {
        'exception_text': {'string': 'Exception', 'type':'text' },
    }

    ############################################################################
    # CHECK OPERATIONS
    ############################################################################

    def _check_invalid_period_moves(self, cr, uid, fyc, data, context):
        """
        Checks for moves with invalid period on the fiscal year that is being closed
        """
        pool = pooler.get_pool(cr.dbname)
        data['process_task_progress'] = 0.0

        # Consider all the periods of the fiscal year.
        period_ids = [period.id for period in fyc.closing_fiscalyear_id.period_ids]

        # Find moves on the closing fiscal year with dates of previous years
        account_move_ids = pool.get('account.move').search(cr, uid, [
                                ('period_id', 'in', period_ids),
                                ('date', '<', fyc.closing_fiscalyear_id.date_start),
                            ], context=context)

        # Find moves on the closing fiscal year with dates of next years
        account_move_ids.extend(pool.get('account.move').search(cr, uid, [
                                ('period_id', 'in', period_ids),
                                ('date', '>', fyc.closing_fiscalyear_id.date_stop),
                            ], context=context))

        # Find moves not on the closing fiscal year with dates on its year
        account_move_ids.extend(pool.get('account.move').search(cr, uid, [
                                ('period_id', 'not in', period_ids),
                                ('date', '>=', fyc.closing_fiscalyear_id.date_start),
                                ('date', '<=', fyc.closing_fiscalyear_id.date_stop),
                            ], context=context))

        #
        # If one or more moves where found, raise an exception
        #
        if len(account_move_ids):
            invalid_period_moves = pool.get('account.move').read(cr, uid, account_move_ids, ['id', 'date', 'name', 'ref'], context)
            str_invalid_period_moves = '\n'.join(['id: %s, date: %s, number: %s, ref: %s' % (move['id'], move['date'], move['name'], move['ref']) for move in invalid_period_moves])
            raise wizard.except_wizard(_('Error'), _('One or more moves with invalid period or date found on the fiscal year: \n%s') % str_invalid_period_moves)

        data['process_task_progress'] = 100.0


    def _check_draft_moves(self, cr, uid, fyc, data, context):
        """
        Checks for draft moves on the fiscal year that is being closed
        """
        pool = pooler.get_pool(cr.dbname)
        data['process_task_progress'] = 0.0

        #
        # Consider all the periods of the fiscal year *BUT* the L&P,
        # Net L&P and the Closing one.
        #
        period_ids = []
        for period in fyc.closing_fiscalyear_id.period_ids:
            if period.id != fyc.lp_period_id.id \
                    and period.id != fyc.nlp_period_id.id \
                    and period.id != fyc.c_period_id.id:
                period_ids.append(period.id)

        # Find the moves on the given periods
        account_move_ids = pool.get('account.move').search(cr, uid, [
                                ('period_id', 'in', period_ids),
                                ('state', '=', 'draft'),
                            ], context=context)

        #
        # If one or more draft moves where found, raise an exception
        #
        if len(account_move_ids):
            draft_moves = pool.get('account.move').read(cr, uid, account_move_ids, ['id', 'date', 'name', 'ref'], context)
            str_draft_moves = '\n'.join(['id: %s, date: %s, number: %s, ref: %s' % (move['id'], move['date'], move['name'], move['ref']) for move in draft_moves])
            raise wizard.except_wizard(_('Error'), _('One or more draft moves found: \n%s') % str_draft_moves)

        data['process_task_progress'] = 100.0


    def _check_unbalanced_moves(self, cr, uid, fyc, data, context):
        """
        Checks for unbalanced moves on the fiscal year that is being closed
        """
        pool = pooler.get_pool(cr.dbname)
        data['process_task_progress'] = 0.0

        #
        # Consider all the periods of the fiscal year *BUT* the L&P,
        # Net L&P and the Closing one.
        #
        period_ids = []
        for period in fyc.closing_fiscalyear_id.period_ids:
            if period.id != fyc.lp_period_id.id \
                    and period.id != fyc.nlp_period_id.id \
                    and period.id != fyc.c_period_id.id:
                period_ids.append(period.id)

        # Find the moves on the given periods
        account_move_ids = pool.get('account.move').search(cr, uid, [
                                ('period_id', 'in', period_ids),
                                ('state', '!=', 'draft'),
                            ], context=context)

        #
        # For each found move, check it
        #
        unbalanced_moves = []
        total_accounts = len(account_move_ids)
        accounts_done = 0
        for move in pool.get('account.move').read(cr, uid, account_move_ids, ['line_id'], context):
            amount = 0
            for line in pool.get('account.move.line').read(cr, uid, move['line_id'], ['debit', 'credit'], context):
                amount += (line['debit'] - line['credit'])

            if abs(amount) > 0.5 * 10 ** -int(config['price_accuracy']):
                unbalanced_moves.append(move)

            accounts_done += 1
            data['process_task_progress'] = (accounts_done * 90.0) / total_accounts

        #
        # If one or more unbalanced moves where found, raise an exception
        #
        if len(unbalanced_moves):
            str_unbalanced_moves = '\n'.join(['id: %s, date: %s, number: %s, ref: %s' % (move.id, move.date, move.name, move.ref) for move in unbalanced_moves])
            raise wizard.except_wizard(_('Error'), _('One or more unbalanced moves found: \n%s') % str_unbalanced_moves)

        data['process_task_progress'] = 100.0



    ############################################################################
    # CLOSING/OPENING OPERATIONS
    ############################################################################

    def create_closing_move(self, cr, uid, operation, fyc, data, context):
        """
        Create a closing move (L&P, NL&P or Closing move).
        """
        pool = pooler.get_pool(cr.dbname)

        data['process_task_progress'] = 0.0

        move_lines = []
        dest_accounts_totals = {}
        period_ids = []
        account_mapping_ids = []
        description = None
        date = None
        period_id = None
        journal_id = None
        fiscalyear_id = fyc.closing_fiscalyear_id.id

        #
        # Depending on the operation we will use different data
        #
        if operation == 'loss_and_profit':
            #
            # Consider all the periods of the fiscal year *BUT* the L&P,
            # Net L&P and the Closing one.
            #
            for period in fyc.closing_fiscalyear_id.period_ids:
                if period.id != fyc.lp_period_id.id \
                        and period.id != fyc.nlp_period_id.id \
                        and period.id != fyc.c_period_id.id:
                    period_ids.append(period.id)
            #
            # Set the accounts to use
            #
            account_mapping_ids = fyc.lp_account_mapping_ids
            for account_map in account_mapping_ids:
                if not account_map.dest_account_id:
                    raise wizard.except_wizard(_('UserError'), _("The L&P account mappings are not properly configured: %s") % account_map.name)

            #
            # Get the values for the lines
            #
            if not fyc.lp_description:
                raise wizard.except_wizard(_('UserError'), _("The L&P description must be defined"))
            if not fyc.lp_date:
                raise wizard.except_wizard(_('UserError'), _("The L&P date must be defined"))
            if not (fyc.lp_period_id and fyc.lp_period_id.id):
                raise wizard.except_wizard(_('UserError'), _("The L&P period must be defined"))
            if not (fyc.lp_journal_id and fyc.lp_journal_id.id):
                raise wizard.except_wizard(_('UserError'), _("The L&P journal must be defined"))
            description = fyc.lp_description
            date = fyc.lp_date
            period_id = fyc.lp_period_id.id
            journal_id = fyc.lp_journal_id.id
        elif operation == 'net_loss_and_profit':
            #
            # Consider all the periods of the fiscal year *BUT* the 
            # Net L&P and the Closing one.
            #
            for period in fyc.closing_fiscalyear_id.period_ids:
                if period.id != fyc.nlp_period_id.id \
                        and period.id != fyc.c_period_id.id:
                    period_ids.append(period.id)
            #
            # Set the accounts to use
            #
            account_mapping_ids = fyc.nlp_account_mapping_ids
            for account_map in account_mapping_ids:
                if not account_map.dest_account_id:
                    raise wizard.except_wizard(_('UserError'), _("The Net L&P account mappings are not properly configured: %s") % account_map.name)
            #
            # Get the values for the lines
            #
            if not fyc.nlp_description:
                raise wizard.except_wizard(_('UserError'), _("The Net L&P description must be defined"))
            if not fyc.nlp_date:
                raise wizard.except_wizard(_('UserError'), _("The Net L&P date must be defined"))
            if not (fyc.nlp_period_id and fyc.nlp_period_id.id):
                raise wizard.except_wizard(_('UserError'), _("The Net L&P period must be defined"))
            if not (fyc.nlp_journal_id and fyc.nlp_journal_id.id):
                raise wizard.except_wizard(_('UserError'), _("The Net L&P journal must be defined"))
            description = fyc.nlp_description
            date = fyc.nlp_date
            period_id = fyc.nlp_period_id.id
            journal_id = fyc.nlp_journal_id.id
        elif operation == 'close':
            # Require the user to have performed the L&P operation
            if not (fyc.loss_and_profit_move_id and fyc.loss_and_profit_move_id.id):
                raise wizard.except_wizard(_('UserError'), _("The L&P move must exist before creating the closing one"))
            #
            # Consider all the periods of the fiscal year *BUT* the Closing one.
            #
            for period in fyc.closing_fiscalyear_id.period_ids:
                if period.id != fyc.c_period_id.id:
                    period_ids.append(period.id)
            # Set the accounts to use
            account_mapping_ids = fyc.c_account_mapping_ids
            #
            # Get the values for the lines
            #
            if not fyc.c_description:
                raise wizard.except_wizard(_('UserError'), _("The closing description must be defined"))
            if not fyc.c_date:
                raise wizard.except_wizard(_('UserError'), _("The closing date must be defined"))
            if not (fyc.c_period_id and fyc.c_period_id.id):
                raise wizard.except_wizard(_('UserError'), _("The closing period must be defined"))
            if not (fyc.c_journal_id and fyc.c_journal_id.id):
                raise wizard.except_wizard(_('UserError'), _("The closing journal must be defined"))
            description = fyc.c_description
            date = fyc.c_date
            period_id = fyc.c_period_id.id
            journal_id = fyc.c_journal_id.id
        else:
            assert operation in ('loss_and_profit', 'net_loss_and_profit', 'close'), "The operation must be a supported one"


        #
        # For each (parent) account in the mapping list
        #
        total_accounts = len(account_mapping_ids)
        accounts_done = 0
        for account_map in account_mapping_ids:
            # Init (if needed) the dictionary that will store the totals for the dest accounts
            if account_map.dest_account_id:
                dest_accounts_totals[account_map.dest_account_id.id] = dest_accounts_totals.get(account_map.dest_account_id.id, 0)

            # Find its children accounts (recursively)
            # FIXME: _get_children_and_consol is a protected member of account_account but the OpenERP code base uses it like this :(
            child_ids = pool.get('account.account')._get_children_and_consol(cr, uid, [account_map.source_account_id.id], context)

            # For each children account. (Notice the context filter! the computed balanced is based on this filter)
            for account in pool.get('account.account').read(cr, uid, child_ids, ['id', 'type', 'balance'], context={'fiscalyear': fiscalyear_id, 'periods': period_ids}):
                # Check if the children account needs to (and can) be closed
                # Note: We currently ignore the close_method (account.user_type.close_method)
                #       and always do a balance close.
                if account['type'] != 'view':
                    # Compute the balance for the account (uses the previous browse context filter)
                    balance = account['balance']
                    # Check if the balance is greater than the limit
                    if abs(balance) >= 0.5 * 10 ** -int(config['price_accuracy']):
                        #
                        # Add a new line to the move
                        #
                        move_lines.append({
                                'account_id': account['id'],
                                'debit': balance<0 and -balance,
                                'credit': balance>0 and balance,
                                'name': description,
                                'date': date,
                                'period_id': period_id,
                                'journal_id': journal_id,
                            })

                        # Update the dest account total (with the inverse of the balance)
                        if account_map.dest_account_id:
                            dest_accounts_totals[account_map.dest_account_id.id] -= balance
            accounts_done += 1
            data['process_task_progress'] = (accounts_done * 90.0) / total_accounts

        #
        # Add the dest lines
        #
        for dest_account_id in dest_accounts_totals:
            balance = dest_accounts_totals[dest_account_id]
            move_lines.append({
                    'account_id': dest_account_id,
                    'debit': balance<0 and -balance,
                    'credit': balance>0 and balance,
                    'name': description,
                    'date': date,
                    'period_id': period_id,
                    'journal_id': journal_id,
                })
        data['process_task_progress'] = 95.0

        #
        # Finally create the account move with all the lines (if needed)
        #
        if move_lines:
            # Firstly we create the move
            move_id = pool.get('account.move').create(cr, uid, {
                            'ref': description,
                            'date': date,
                            'period_id': period_id,
                            'journal_id': journal_id,
                        }, context=context)
            for move in move_lines:
                move['move_id'] = move_id
                pool.get('account.move.line').create(cr, uid, move,
                                                     context=context,
                                                     check=False)
            journal = pool.get('account.journal').read(cr, uid, journal_id, ['name', 'entry_posted'])
            if journal['entry_posted']:
                pool.get('account.move').button_validate(cr,uid, [move_id],context)
        else:
            move_id = None
        data['process_task_progress'] = 99.0

        #
        # Save the reference to the created account move into the fyc object
        #
        if operation == 'loss_and_profit':
            pool.get('l10n_es_cierre_ejercicio.fyc').write(cr, uid, [fyc.id], { 'loss_and_profit_move_id': move_id })
        elif operation == 'net_loss_and_profit':
            pool.get('l10n_es_cierre_ejercicio.fyc').write(cr, uid, [fyc.id], { 'net_loss_and_profit_move_id': move_id })
        elif operation == 'close':
            pool.get('l10n_es_cierre_ejercicio.fyc').write(cr, uid, [fyc.id], { 'closing_move_id': move_id })
        else:
            assert operation in ('loss_and_profit', 'net_loss_and_profit', 'close'), "The operation must be a supported one"

        data['process_task_progress'] = 100.0
        return move_id


    def create_opening_move(self, cr, uid, operation, fyc, data, context):
        """
        Create an opening move (based on the closing one)
        """
        pool = pooler.get_pool(cr.dbname)
        data['process_task_progress'] = 0.0

        move_lines = []
        description = None
        date = None
        period_id = None
        journal_id = None
        closing_move = None

        #
        # Depending on the operation we will use one or other closing move
        # as the base for the opening move.
        # Note: Yes, currently only one 'closing' move exists,
        #       but I want this to be extensible :)
        #
        if operation == 'open':
            closing_move = fyc.closing_move_id
            # Require the user to have performed the closing operation
            if not (closing_move and closing_move.id):
                raise wizard.except_wizard(_('UserError'), _("The closing move must exist to create the opening one"))
            if not closing_move.line_id:
                raise wizard.except_wizard(_('UserError'), _("The closing move shouldn't be empty"))
            #
            # Get the values for the lines
            #
            if not fyc.o_description:
                raise wizard.except_wizard(_('UserError'), _("The opening description must be defined"))
            if not fyc.o_date:
                raise wizard.except_wizard(_('UserError'), _("The opening date must be defined"))
            if not (fyc.o_period_id and fyc.o_period_id.id):
                raise wizard.except_wizard(_('UserError'), _("The opening period must be defined"))
            if not (fyc.o_journal_id and fyc.o_journal_id.id):
                raise wizard.except_wizard(_('UserError'), _("The opening journal must be defined"))
            description = fyc.o_description
            date = fyc.o_date
            period_id = fyc.o_period_id.id
            journal_id = fyc.o_journal_id.id
        else:
            assert operation in ('open'), "The operation must be a supported one"

        #
        # Read the lines from the closing move, and append the inverse lines
        # to the opening move lines.
        #
        total_accounts = len(closing_move.line_id)
        accounts_done = 0
        for line in closing_move.line_id:
            move_lines.append({
                    'account_id': line.account_id.id,
                    'debit': line.credit,
                    'credit': line.debit,
                    'name': description,
                    'date': date,
                    'period_id': period_id,
                    'journal_id': journal_id,
                })
            accounts_done += 1
            data['process_task_progress'] = (accounts_done * 90.0) / total_accounts

        #
        # Finally create the account move with all the lines (if needed)
        #
        if move_lines:
            # Firstly we create the move
            move_id = pool.get('account.move').create(cr, uid, {
                            'ref': description,
                            'date': date,
                            'period_id': period_id,
                            'journal_id': journal_id,
                        }, context=context)
            for move in move_lines:
                move['move_id'] = move_id
                pool.get('account.move.line').create(cr, uid, move,
                                                     context=context,
                                                     check=False)
            journal = pool.get('account.journal').read(cr, uid, journal_id, ['name', 'entry_posted'])
            if journal['entry_posted']:
                pool.get('account.move').button_validate(cr,uid, [move_id],context)
        else:
            move_id = None
        data['process_task_progress'] = 99.0

        #
        # Save the reference to the created account move into the fyc object
        #
        if operation == 'open':
            pool.get('l10n_es_cierre_ejercicio.fyc').write(cr, uid, [fyc.id], { 'opening_move_id': move_id })
        else:
            assert operation in ('open'), "The operation must be a supported one"

        data['process_task_progress'] = 100.0
        return move_id


    def remove_move(self, cr, uid, operation, fyc, data, context):
        """
        Remove a account move (L&P, NL&P, Closing or Opening move)
        """
        pool = pooler.get_pool(cr.dbname)
        data['process_task_progress'] = 0.0

        #
        # Depending on the operation we will delete one or other move
        #
        move = None
        if operation == 'loss_and_profit':
            move = fyc.loss_and_profit_move_id
            pool.get('l10n_es_cierre_ejercicio.fyc').write(cr, uid, fyc.id, { 'loss_and_profit_move_id': None })
        elif operation == 'net_loss_and_profit':
            move = fyc.net_loss_and_profit_move_id
            pool.get('l10n_es_cierre_ejercicio.fyc').write(cr, uid, fyc.id, { 'net_loss_and_profit_move_id': None })
        elif operation == 'close':
            move = fyc.closing_move_id
            pool.get('l10n_es_cierre_ejercicio.fyc').write(cr, uid, fyc.id, { 'closing_move_id': None })
        elif operation == 'open':
            move = fyc.opening_move_id
            pool.get('l10n_es_cierre_ejercicio.fyc').write(cr, uid, fyc.id, { 'opening_move_id': None })
        else:
            assert operation in ('loss_and_profit', 'net_loss_and_profit', 'close', 'open'), "The operation must be a supported one"
        data['process_task_progress'] = 15.0

        assert move and move.id, "The move to delete must be defined"

        #
        # Unreconcile the move if needed
        #
        reconcile_ids = []
        for line in move.line_id:
            if line.reconcile_id and (line.reconcile_id.id not in reconcile_ids):
                reconcile_ids.append(line.reconcile_id.id)
            if line.reconcile_partial_id and (line.reconcile_partial_id.id not in reconcile_ids):
                reconcile_ids.append(line.reconcile_partial_id.id)
        if reconcile_ids:
            pool.get('account.move.reconcile').unlink(cr, uid, reconcile_ids, context)
        data['process_task_progress'] = 30.0

        #
        # Remove the move after changing it's state to draft
        #
        pool.get('account.move').write(cr, uid, [move.id], {'state': 'draft'}, context)
        pool.get('account.move').unlink(cr, uid, [move.id], context)

        data['process_task_progress'] = 100.0
        return move.id


    ############################################################################
    # Wizard Actions
    ############################################################################

    def _init_choice(self, cr, uid, data, context):
        """
        Choice-like action that checks whether the operations must be run
        or canceled.
        """
        if context is None:
            context = {}
        if context.get('cancel_mode'):
            data['cancel_mode'] = True
            return 'init_cancel'
        else:
            data['cancel_mode'] = False
            return 'init_run'
        

    def _run(self, db_name, uid, data, context=None):
        """
        Creates / removes FYC entries
        """
        data['process_progress'] = 0
        data['process_task_progress'] = 0
        data['process_task'] = None
        try:
            conn = sql_db.db_connect(db_name)
            cr = conn.cursor()
            pool = pooler.get_pool(cr.dbname)

            #
            # If the wizard is in cancel mode, run the objects cancel action
            # to let it undo the confirmation action, before running the wizard.
            #
            if data.get('cancel_mode'):
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_validate(uid, 'l10n_es_cierre_ejercicio.fyc', data['id'], 'cancel', cr)

            # Read the object
            fyc = pool.get('l10n_es_cierre_ejercicio.fyc').browse(cr, uid, data['id'], context=context)

            #
            # Calculate the operations to perform (needed to calculate the progress)
            #
            total_operations = 0
            operations_done = 0
            if fyc.check_invalid_period_moves:
                total_operations += 1
            if fyc.check_draft_moves:
                total_operations += 1
            if fyc.check_unbalanced_moves:
                total_operations += 1
            if (fyc.create_loss_and_profit and not fyc.loss_and_profit_move_id) \
                or ((not fyc.create_loss_and_profit) and fyc.loss_and_profit_move_id):
                total_operations += 1
            if (fyc.create_net_loss_and_profit and not fyc.net_loss_and_profit_move_id) \
                or ((not fyc.create_net_loss_and_profit) and fyc.net_loss_and_profit_move_id):
                total_operations += 1
            if (fyc.create_closing and not fyc.closing_move_id) \
                or ((not fyc.create_closing) and fyc.closing_move_id):
                total_operations += 1
            if (fyc.create_opening and not fyc.opening_move_id) \
                or ((not fyc.create_opening) and fyc.opening_move_id):
                total_operations += 1
                
            if total_operations > 0:
                #
                # Check for invalid period moves if needed
                #
                if fyc.check_invalid_period_moves:
                    data['process_task'] = 'Check invalid period/date moves'
                    self._check_invalid_period_moves(cr, uid, fyc, data, context)
                    operations_done += 1
                    data['process_progress'] = (operations_done * 100.0) / total_operations

                #
                # Check for draft moves if needed
                #
                if fyc.check_draft_moves:
                    data['process_task'] = 'Check draft moves'
                    self._check_draft_moves(cr, uid, fyc, data, context)
                    operations_done += 1
                    data['process_progress'] = (operations_done * 100.0) / total_operations

                #
                # Check for unbalanced moves if needed
                #
                if fyc.check_unbalanced_moves:
                    data['process_task'] = 'Check unbalanced moves'
                    self._check_unbalanced_moves(cr, uid, fyc, data, context)
                    operations_done += 1
                    data['process_progress'] = (operations_done * 100.0) / total_operations

                #
                # Create L&P move if needed
                #
                if fyc.create_loss_and_profit and not fyc.loss_and_profit_move_id:
                    data['process_task'] = 'Create L&P move'
                    self.create_closing_move(cr, uid, 'loss_and_profit', fyc, data, context)
                    operations_done += 1
                    data['process_progress'] = (operations_done * 100.0) / total_operations
                #
                # Remove the L&P move if needed
                #
                if (not fyc.create_loss_and_profit) and fyc.loss_and_profit_move_id:
                    data['process_task'] = 'Remove L&P move'
                    self.remove_move(cr, uid, 'loss_and_profit', fyc, data, context)
                    operations_done += 1
                    data['process_progress'] = (operations_done * 100.0) / total_operations

                # Refresh the cached fyc object
                fyc = pool.get('l10n_es_cierre_ejercicio.fyc').browse(cr, uid, data['id'], context=context)


                #
                # Create the Net L&P move if needed
                #
                if fyc.create_net_loss_and_profit and not fyc.net_loss_and_profit_move_id:
                    data['process_task'] = 'Create NL&P move'
                    self.create_closing_move(cr, uid, 'net_loss_and_profit', fyc, data, context)
                    operations_done += 1
                    data['process_progress'] = (operations_done * 100.0) / total_operations
                #
                # Remove the Net L&P move if needed
                #
                if (not fyc.create_net_loss_and_profit) and fyc.net_loss_and_profit_move_id:
                    data['process_task'] = 'Remove NL&P move'
                    self.remove_move(cr, uid, 'net_loss_and_profit', fyc, data, context)
                    operations_done += 1
                    data['process_progress'] = (operations_done * 100.0) / total_operations

                # Refresh the cached fyc object
                fyc = pool.get('l10n_es_cierre_ejercicio.fyc').browse(cr, uid, data['id'], context=context)


                #
                # Create the closing move if needed
                #
                if fyc.create_closing and not fyc.closing_move_id:
                    data['process_task'] = 'Create closing move'
                    self.create_closing_move(cr, uid, 'close', fyc, data, context)
                    operations_done += 1
                    data['process_progress'] = (operations_done * 100.0) / total_operations
                #
                # Remove the closing move if needed
                #
                if (not fyc.create_closing) and fyc.closing_move_id:
                    data['process_task'] = 'Remove closing move'
                    self.remove_move(cr, uid, 'close', fyc, data, context)
                    operations_done += 1
                    data['process_progress'] = (operations_done * 100.0) / total_operations

                # Refresh the cached fyc object
                fyc = pool.get('l10n_es_cierre_ejercicio.fyc').browse(cr, uid, data['id'], context=context)

                
                #
                # Create the opening move if needed
                #
                if fyc.create_opening and not fyc.opening_move_id:
                    data['process_task'] = 'Create opening move'
                    self.create_opening_move(cr, uid, 'open', fyc, data, context)
                    operations_done += 1
                    data['process_progress'] = (operations_done * 100.0) / total_operations
                #
                # Remove the opening move if needed
                #
                if (not fyc.create_opening) and fyc.opening_move_id:
                    data['process_task'] = 'Remove opening move'
                    self.remove_move(cr, uid, 'open', fyc, data, context)
                    operations_done += 1
                    data['process_progress'] = (operations_done * 100.0) / total_operations

            #
            # Set the as done (if not in cancel_mode)
            #
            if not data.get('cancel_mode'):
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_validate(uid, 'l10n_es_cierre_ejercicio.fyc', fyc.id, 'run', cr)

            data['process_progress'] = 100
            cr.commit()
        except Exception, ex:
            data['process_exception'] = ex
            cr.rollback()
            raise
        finally:
            cr.close()
            data['process_done'] = True
        return {}


    def _run_in_background_choice(self, cr, uid, data, context):
        """
        Choice-like action that runs the process on background,
        waiting for it to end or timeout.
        """
        if not data.get('process_thread'):
            # Run the calculation in background
            data['process_done'] = False
            data['process_exception'] = None
            data['process_thread'] = threading.Thread(target=self._run, args=(cr.dbname, uid, data, context))
            data['process_thread'].start()
        #
        # Wait up some seconds seconds for the task to end.
        #
        time_left = 20
        while not data['process_done'] and time_left > 0:
            time_left = time_left - 1
            time.sleep(1)
            message = "Fiscal year closing progress: %s%% (%s: %s%%)" % (data.get('process_progress'), data.get('process_task'), data.get('process_task_progress'))
            netsvc.Logger().notifyChannel('fyc', netsvc.LOG_DEBUG, message)
        #
        # Check if we are done
        #
        if data['process_done']:
            if data['process_exception']:
                return 'show_exception'
            else:
                return 'done'
        else:
            return 'progress'


    def _progress_action(self, cr, uid, data, context):
        """
        Action that gets the current progress
        """
        return {
            'task_progress': data['process_task_progress'],
            'progress': data['process_progress']
        }

    def _show_exception_action(self, cr, uid, data, context):
        """
        Action that gets the calculation exception text
        """
        exception_text = ''
        if data.get('process_exception'):
            if isinstance(data['process_exception'], wizard.except_wizard):
                exception_text = data['process_exception'].value
            else:
                try:
                    exception_text = unicode(data['process_exception'])
                except:
                    exception_text = str(data['process_exception'])
        return { 'exception_text': exception_text }

    ############################################################################
    # States
    ############################################################################

    states = {
        'init': {
            'actions': [],
            'result': {'type': 'choice', 'next_state': _init_choice}
        },
        'init_run': {
            'actions': [],
            'result': {'type':'form', 'arch': _init_run_form, 'fields': {}, 'state':[('end', 'Cancel', 'gtk-cancel', True), ('run', 'Run', 'gtk-apply', True)]}
        },
        'init_cancel': {
            'actions': [],
            'result': {'type':'form', 'arch': _init_cancel_form, 'fields': {}, 'state':[('end', 'Cancel', 'gtk-cancel', True), ('run', 'Run', 'gtk-apply', True)]}
        },
        'run': {
            'actions': [],
            'result': {'type': 'choice', 'next_state': _run_in_background_choice}
        },
        'progress': {
            'actions': [_progress_action],
            'result': {'type': 'form', 'arch': _progress_form, 'fields': _progress_fields, 'state':[('end','Close (continues in background)', 'gtk-cancel', True),('run','Keep waiting', 'gtk-go-forward', True)]}
        },
        'done': {
            'actions': [],
            'result': {'type': 'form', 'arch': _done_form, 'fields': {}, 'state':[('end','Done', 'gtk-ok', True)]}
        },
        'show_exception': {
            'actions': [_show_exception_action],
            'result': {'type': 'form', 'arch': _show_exception_form, 'fields': _show_exception_fields, 'state':[('end','Done', 'gtk-ok', True)]}
        }
    }


wizard_run('l10n_es_cierre_ejercicio.wizard_run')


class wizard_cancel(wizard_run):
    """
    Wizard to remove the FYC entries.
    """

    def _init_choice(self, cr, uid, data, context):
        """
        Choice-like action that checks whether the operations must be run
        or canceled. => Always cancel on wizard_cancel.
        """
        data['cancel_mode'] = True
        return 'init_cancel'

    states = wizard_run.states.copy()
    
    states['init'] = {
            'actions': [],
            'result': {'type': 'choice', 'next_state': _init_choice}
        }


wizard_cancel('l10n_es_cierre_ejercicio.wizard_cancel')

