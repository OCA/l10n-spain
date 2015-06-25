# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP - Import operations model 347 engine
#    Copyright (C) 2009 Asr Oss. All Rights Reserved
#    Copyright (c) 2012 Servicios Tecnológicos Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2012 Avanzosc (http://www.avanzosc.com)
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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
#############################################################################

from tools.translate import _
from tools import float_is_zero
import pooler
import netsvc
from osv import fields
from osv import osv

class cancel_fyc(osv.osv_memory):
    
    _name="cancel.fyc"
    _description="Cancel the Fiscal Year Closing"
    _columns = {
                'delete_pyg':fields.boolean('Delete P&L'),
                'delete_net_pyg':fields.boolean('Delete Net P&L'),
                'delete_close':fields.boolean('Delete Close'),
                'delete_open':fields.boolean('Delete Open'),               
                }

    def view_init(self, cr, uid, fields, context=None):
        if context is None:
            context={}

        fyc_ids =  context.get('active_ids',[])
        self.pool.get('l10n_es_fiscal_year_closing.fyc').write(cr,uid,fyc_ids,{'create_loss_and_profit': False,
                    'create_net_loss_and_profit': False,
                    'create_closing': False,
                    'create_opening': False,
                    'check_invalid_period_moves': False,
                    'check_draft_moves': False,
                    'check_unbalanced_moves': False,
                }, context=context)

        return True
    
    def default_get(self, cr, uid, fields, context=None):
        """
        This function gets default values
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param fields: List of fields for default value
        @param context: A standard dictionary for contextual values

        @return : default values of fields.
        """
        record_id = context and context.get('active_id', False) or False
        res = super(cancel_fyc, self).default_get(cr, uid, fields, context=context)
        fyc = self.pool.get('l10n_es_fiscal_year_closing.fyc').browse(cr,uid,record_id)
        if record_id:
            res['delete_pyg'] = bool(fyc.loss_and_profit_move_id)
            res['delete_net_pyg'] = bool(fyc.net_loss_and_profit_move_id)
            res['delete_close'] = bool(fyc.closing_move_id)
            res['delete_open'] = bool(fyc.opening_move_id)
        return res
        
    def _remove_move(self, cr, uid, move, context):
        """
        Remove an account move, removing reconciles if any
        """
        # Unreconcile the move if needed
        reconcile_ids = []
        for line in move.line_id:
            if line.reconcile_id and (line.reconcile_id.id not in reconcile_ids):
                reconcile_ids.append(line.reconcile_id.id)
            if line.reconcile_partial_id and (line.reconcile_partial_id.id not in reconcile_ids):
                reconcile_ids.append(line.reconcile_partial_id.id)
        if reconcile_ids:
            self.pool.get('account.move.reconcile').unlink(cr, uid, reconcile_ids, context)

        obj_move = self.pool.get('account.move')
        obj_move_line = self.pool.get('account.move.line')
        # Remove the move after changing it's state to draft
        obj_move.write(cr, uid, [move.id], {'state': 'draft'}, context)
        # Done in this way for performance reasons
        line_ids = map(lambda x: x.id, move.line_id)
        obj_move_line.unlink(cr, uid, line_ids, context=context, check=False)
        obj_move.unlink(cr, uid, [move.id], context)

        return move.id
    
    def cancel_run(self, cr, uid, data, context=None):
        try:
            # If the wizard is in cancel mode, run the objects cancel action
            # to let it undo the confirmation action, before running the wizard.
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'l10n_es_fiscal_year_closing.fyc', context['active_id'], 'cancel', cr)

            # Read the object
            fyc_obj = self.pool.get('l10n_es_fiscal_year_closing.fyc')
            fyc = fyc_obj.browse(cr, uid, context['active_id'], context=context)
            result = {}
            if fyc.loss_and_profit_move_id or fyc.net_loss_and_profit_move_id or fyc.closing_move_id or fyc.opening_move_id:
                # Remove the L&P move if needed
                if fyc.loss_and_profit_move_id:
                    self._remove_move(cr, uid, fyc.loss_and_profit_move_id, context)
                    result['loss_and_profit_move_id'] = None
                # Remove the Net L&P move if needed
                if fyc.net_loss_and_profit_move_id:
                    self._remove_move(cr, uid, fyc.net_loss_and_profit_move_id, context)
                    result['net_loss_and_profit_move_id'] = None
                # Remove the closing move if needed
                if fyc.closing_move_id:
                    self._remove_move(cr, uid, fyc.closing_move_id, context)
                    result['closing_move_id'] = None
                # Remove the opening move if needed
                if (not fyc.create_opening) and fyc.opening_move_id:
                    self._remove_move(cr, uid, fyc.opening_move_id, context)
                    result['opening_move_id'] = None
            fyc_obj.write(cr, uid, [fyc.id], result, context)

            cr.commit()
        except Exception:
            cr.rollback()
            raise
        return {'type': 'ir.actions.act_window_close'}

cancel_fyc()

class execute_fyc(osv.osv_memory):
    
    _name='execute.fyc'
    _description="Execute the Fiscal Year Closing"
    
    _columns = {
                'delete_pyg':fields.boolean('Delete P&L'),
                'delete_net_pyg':fields.boolean('Delete Net P&L'),
                'delete_close':fields.boolean('Delete Close'),
                'delete_open':fields.boolean('Delete Open'), 
                'create_pyg':fields.boolean('Create P&L'),
                'create_net_pyg':fields.boolean('Create Net P&L'),
                'create_close':fields.boolean('Create Close'),
                'create_open':fields.boolean('Create Open'), 
                'check_draft':fields.boolean('Check Draft'),
                'check_unbalanced':fields.boolean('Check Unbalanced Moves'),  
                'check_invalid':fields.boolean('Check Invalid Periods or Date Moves'),             
                }
    
    def default_get(self, cr, uid, fields, context=None):
        """
        This function gets default values
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param fields: List of fields for default value
        @param context: A standard dictionary for contextual values

        @return : default values of fields.
        """
        record_id = context and context.get('active_id', False) or False
        res = super(execute_fyc, self).default_get(cr, uid, fields, context=context)
        fyc = self.pool.get('l10n_es_fiscal_year_closing.fyc').browse(cr,uid,record_id)
        if record_id:
            if 'delete_pyg' in fields:
                bool1=False
                if (not fyc.create_loss_and_profit) and fyc.loss_and_profit_move_id:
                    bool1=True
                res.update({'delete_pyg': bool1})
            if 'create_pyg' in fields:
                bool11=False
                if fyc.create_loss_and_profit and (not fyc.loss_and_profit_move_id):
                    bool11=True
                res.update({'create_pyg': bool11})
                
            if 'delete_net_pyg' in fields:
                bool2=False
                if (not fyc.create_net_loss_and_profit) and fyc.net_loss_and_profit_move_id:
                    bool2=True
                res.update({'delete_net_pyg':bool2 })
            if 'create_net_pyg' in fields:
                bool21=False
                if (not fyc.net_loss_and_profit_move_id) and fyc.create_net_loss_and_profit:
                    bool21=True
                res.update({'create_net_pyg':bool21 })
                
            if 'delete_close' in fields:
                bool3=False
                if fyc.closing_move_id and (not fyc.create_closing):
                    bool3=True
                res.update({'delete_close': bool3})
            if 'create_close' in fields:
                bool31=False
                if (not fyc.closing_move_id) and fyc.create_closing:
                    bool31=True
                res.update({'create_close': bool31})    
                
            if 'delete_open' in fields:
                bool4=False
                if fyc.opening_move_id and (not fyc.create_opening):
                    bool4=True
                res.update({'delete_open': bool4})
            if 'create_open' in fields:
                bool41=False
                if (not fyc.opening_move_id) and fyc.create_opening:
                    bool41=True
                res.update({'create_open': bool41})
                
                 
            if 'check_draft' in fields:
                bool5=False
                if fyc.check_draft_moves:
                    bool5=True
                res.update({'check_draft': bool5}) 
            if 'check_unbalanced' in fields:
                bool6=False
                if fyc.check_unbalanced_moves:
                    bool6=True
                res.update({'check_unbalanced': bool6}) 
            if 'check_invalid' in fields:
                bool7=False
                if fyc.check_invalid_period_moves:
                    bool7=True
                res.update({'check_invalid': bool7}) 
        return res

    def remove_move(self, cr, uid, operation, fyc, context):
        """
        Remove a account move (L&P, NL&P, Closing or Opening move)
        """
        pool = pooler.get_pool(cr.dbname)

        fyc_obj=pool.get('l10n_es_fiscal_year_closing.fyc')
        #
        # Depending on the operation we will delete one or other move
        #
        move = None
        if operation == 'loss_and_profit':
            move = fyc.loss_and_profit_move_id
            fyc_obj.write(cr, uid, fyc.id, { 'loss_and_profit_move_id': None })
        elif operation == 'net_loss_and_profit':
            move = fyc.net_loss_and_profit_move_id
            fyc_obj.write(cr, uid, fyc.id, { 'net_loss_and_profit_move_id': None })
        elif operation == 'close':
            move = fyc.closing_move_id
            fyc_obj.write(cr, uid, fyc.id, { 'closing_move_id': None })
        elif operation == 'open':
            move = fyc.opening_move_id
            fyc_obj.write(cr, uid, fyc.id, { 'opening_move_id': None })
        else:
            assert operation in ('loss_and_profit', 'net_loss_and_profit', 'close', 'open'), "The operation must be a supported one"

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

        #
        # Remove the move after changing it's state to draft
        #
        pool.get('account.move').write(cr, uid, [move.id], {'state': 'draft'}, context)
        pool.get('account.move').unlink(cr, uid, [move.id], context)

        return move.id

    def _check_invalid_period_moves(self, cr, uid, fyc, context):
        """
        Checks for moves with invalid period on the fiscal year that is being closed
        """
        pool = pooler.get_pool(cr.dbname)

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
            invalid_period_moves = pool.get('account.move').browse(cr, uid, account_move_ids, context)
            str_invalid_period_moves = '\n'.join(['id: %s, date: %s, number: %s, ref: %s' % (move.id, move.date, move.name, move.ref) for move in invalid_period_moves])
            raise osv.except_osv(_('Error'), _('One or more moves with invalid period or date found on the fiscal year: \n%s') % str_invalid_period_moves)

    def _check_draft_moves(self, cr, uid, fyc, context):
        """
        Checks for draft moves on the fiscal year that is being closed
        """
        pool = pooler.get_pool(cr.dbname)

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
                                ('state', '=', 'draft')], context=context)

        #
        # If one or more draft moves where found, raise an exception
        #
        if len(account_move_ids):
            draft_moves = pool.get('account.move').browse(cr, uid, account_move_ids, context)
            str_draft_moves = '\n'.join(['id: %s, date: %s, number: %s, ref: %s' % (move.id, move.date, move.name, move.ref) for move in draft_moves])
            raise osv.except_osv(_('Error'), _('One or more draft moves found: \n%s') % str_draft_moves)

    def _check_unbalanced_moves(self, cr, uid, fyc, context):
        """
        Checks for unbalanced moves on the fiscal year that is being closed
        """
        pool = pooler.get_pool(cr.dbname)
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
        accounts_done = 0
        for move in pool.get('account.move').browse(cr, uid, account_move_ids, context):
            amount = 0
            for line in move.line_id:
                amount += (line.debit - line.credit)

            if round(abs(amount), pool.get('decimal.precision').precision_get(cr, uid, 'Account')) > 0:
                unbalanced_moves.append(move)

            accounts_done += 1

        #
        # If one or more unbalanced moves where found, raise an exception
        #
        if len(unbalanced_moves):
            str_unbalanced_moves = '\n'.join(['id: %s, date: %s, number: %s, ref: %s' % (move.id, move.date, move.name, move.ref) for move in unbalanced_moves])
            raise osv.except_osv(_('Error'), _('One or more unbalanced moves found: \n%s') % str_unbalanced_moves)

    ############################################################################
    # CLOSING/OPENING OPERATIONS
    ############################################################################

    def create_closing_move(self, cr, uid, operation, fyc, context):
        """
        Create a closing move (L&P, NL&P or Closing move).
        """
        pool = pooler.get_pool(cr.dbname)

        move_lines = []
        dest_accounts_totals = {}
        period_ids = []
        account_mapping_ids = []
        description = None
        date = None
        period_id = None
        journal_id = None
        company_id = fyc.company_id.id
        fiscalyear_id = fyc.closing_fiscalyear_id.id
        precision = pool.get('decimal.precision').precision_get(
            cr, uid, 'Account')

        # Depending on the operation we will use different data
        if operation == 'loss_and_profit':
            # Consider all the periods of the fiscal year *BUT* the L&P, Net L&P and the Closing one.
            for period in fyc.closing_fiscalyear_id.period_ids:
                if period.id != fyc.lp_period_id.id \
                        and period.id != fyc.nlp_period_id.id \
                        and period.id != fyc.c_period_id.id:
                    period_ids.append(period.id)
            # Set the accounts to use
            account_mapping_ids = fyc.lp_account_mapping_ids
            for account_map in account_mapping_ids:
                if not account_map.dest_account_id:
                    raise osv.except_osv(_('UserError'), _("The L&P account mappings are not properly configured: %s") % account_map.name)
            # Get the values for the lines
            if not fyc.lp_description:
                raise osv.except_osv(_('UserError'), _("The L&P description must be defined"))
            if not fyc.lp_date:
                raise osv.except_osv(_('UserError'), _("The L&P date must be defined"))
            if not (fyc.lp_period_id and fyc.lp_period_id.id):
                raise osv.except_osv(_('UserError'), _("The L&P period must be defined"))
            if not (fyc.lp_journal_id and fyc.lp_journal_id.id):
                raise osv.except_osv(_('UserError'), _("The L&P journal must be defined"))
            description = fyc.lp_description
            date = fyc.lp_date
            period_id = fyc.lp_period_id.id
            journal_id = fyc.lp_journal_id.id
        elif operation == 'net_loss_and_profit':
            # Consider all the periods of the fiscal year *BUT* the Net L&P and the Closing one.
            for period in fyc.closing_fiscalyear_id.period_ids:
                if period.id != fyc.nlp_period_id.id \
                        and period.id != fyc.c_period_id.id:
                    period_ids.append(period.id)
            # Set the accounts to use
            account_mapping_ids = fyc.nlp_account_mapping_ids
            for account_map in account_mapping_ids:
                if not account_map.dest_account_id:
                    raise osv.except_osv(_('UserError'), _("The Net L&P account mappings are not properly configured: %s") % account_map.name)
            # Get the values for the lines
            if not fyc.nlp_description:
                raise osv.except_osv(_('UserError'), _("The Net L&P description must be defined"))
            if not fyc.nlp_date:
                raise osv.except_osv(_('UserError'), _("The Net L&P date must be defined"))
            if not (fyc.nlp_period_id and fyc.nlp_period_id.id):
                raise osv.except_osv(_('UserError'), _("The Net L&P period must be defined"))
            if not (fyc.nlp_journal_id and fyc.nlp_journal_id.id):
                raise osv.except_osv(_('UserError'), _("The Net L&P journal must be defined"))
            description = fyc.nlp_description
            date = fyc.nlp_date
            period_id = fyc.nlp_period_id.id
            journal_id = fyc.nlp_journal_id.id
        elif operation == 'close':
            # Require the user to have performed the L&P operation
            if not (fyc.loss_and_profit_move_id and fyc.loss_and_profit_move_id.id):
                raise osv.except_osv(_('UserError'), _("The L&P move must exist before creating the closing one"))
            # Consider all the periods of the fiscal year *BUT* the Closing one.
            for period in fyc.closing_fiscalyear_id.period_ids:
                if period.id != fyc.c_period_id.id:
                    period_ids.append(period.id)
            # Set the accounts to use
            account_mapping_ids = fyc.c_account_mapping_ids
            # Get the values for the lines
            if not fyc.c_description:
                raise osv.except_osv(_('UserError'), _("The closing description must be defined"))
            if not fyc.c_date:
                raise osv.except_osv(_('UserError'), _("The closing date must be defined"))
            if not (fyc.c_period_id and fyc.c_period_id.id):
                raise osv.except_osv(_('UserError'), _("The closing period must be defined"))
            if not (fyc.c_journal_id and fyc.c_journal_id.id):
                raise osv.except_osv(_('UserError'), _("The closing journal must be defined"))
            description = fyc.c_description
            date = fyc.c_date
            period_id = fyc.c_period_id.id
            journal_id = fyc.c_journal_id.id
        else:
            assert operation in ('loss_and_profit', 'net_loss_and_profit', 'close'), "The operation must be a supported one"

        # For each (parent) account in the mapping list
        for account_map in account_mapping_ids:
            # Init (if needed) the dictionary that will store the totals for the dest accounts
            if account_map.dest_account_id:
                dest_accounts_totals[account_map.dest_account_id.id] = dest_accounts_totals.get(account_map.dest_account_id.id, 0)

            ctx = context.copy()
            ctx.update({'fiscalyear': fiscalyear_id, 'periods': period_ids, 'company_id': company_id})

            # Find its children accounts (recursively)
            # FIXME: _get_children_and_consol is a protected member of account_account, but the OpenERP code base uses it like this :(
            child_ids = pool.get('account.account')._get_children_and_consol(cr, uid, [account_map.source_account_id.id], ctx)
            
            # For each children account. (Notice the context filter! the computed balanced is based on this filter)
            for account in pool.get('account.account').browse(cr, uid, child_ids, ctx):
                # Check if the children account needs to (and can) be closed
                if (account.type != 'view' and not float_is_zero(
                        account.balance, precision_rounding=precision)):
                    if account.user_type.close_method == 'balance':
                        # Compute the balance for the account (uses the previous browse context filter)
                        balance = account.balance
                        # Add a new line to the move
                        move_lines.append({
                                'account_id': account.id,
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
                    elif account.user_type.close_method == 'unreconciled':
                        move_line_obj = pool.get('account.move.line') 
                        found_lines = move_line_obj.search(cr, uid, [ 
                            ('period_id', 'in', period_ids),
                            ('account_id', '=', account.id),
                            ('company_id', '=', company_id),
                            ])
                        lines_by_partner = {}
                        for line in move_line_obj.browse(cr, uid, found_lines):
                            balance = line.debit - line.credit
                            if lines_by_partner.has_key(line.partner_id.id):
                                lines_by_partner[line.partner_id.id] += balance
                            else:
                                lines_by_partner[line.partner_id.id] = balance
                        for partner_id in lines_by_partner.keys():
                            balance = lines_by_partner[partner_id]
                            if not float_is_zero(balance,
                                                 precision_rounding=precision):
                                move_lines.append({
                                    'account_id': account.id,
                                    'debit': balance<0 and -balance,
                                    'credit': balance>0 and balance,
                                    'name': description,
                                    'date': date,
                                    'period_id': period_id,
                                    'journal_id': journal_id,
                                    'partner_id': partner_id,
                                })
                            # Update the dest account total (with the inverse of the balance)
                            if account_map.dest_account_id:
                                dest_accounts_totals[account_map.dest_account_id.id] -= balance
                    elif account.user_type.close_method == 'detail':
                        raise osv.except_osv(_('UserError'), _("Account type closing method is not supported"))
                    else:
                        # Account type has no closing method or method is not listed
                        continue
        # Add the dest lines
        for dest_account_id in dest_accounts_totals.keys():
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
        # Finally create the account move with all the lines (if needed)
        if len(move_lines):
            move_id = pool.get('account.move').create(cr, uid, {
                'line_id': map(lambda x: (0,0,x), move_lines),
                'ref': description,
                'date': date,
                'period_id': period_id,
                'journal_id': journal_id,
                }, context={})
        else:
            move_id = None
        # Save the reference to the created account move into the fyc object
        if operation == 'loss_and_profit':
            pool.get('l10n_es_fiscal_year_closing.fyc').write(cr, uid, [fyc.id], { 'loss_and_profit_move_id': move_id })
        elif operation == 'net_loss_and_profit':
            pool.get('l10n_es_fiscal_year_closing.fyc').write(cr, uid, [fyc.id], { 'net_loss_and_profit_move_id': move_id })
        elif operation == 'close':
            pool.get('l10n_es_fiscal_year_closing.fyc').write(cr, uid, [fyc.id], { 'closing_move_id': move_id })
        else:
            assert operation in ('loss_and_profit', 'net_loss_and_profit', 'close'), "The operation must be a supported one"

        return move_id

    def create_opening_move(self, cr, uid, operation, fyc, context):
        """
        Create an opening move (based on the closing one)
        """
        pool = pooler.get_pool(cr.dbname)

        move_lines = []
        description = None
        date = None
        period_id = None
        journal_id = None

        # Depending on the operation we will use one or other closing move as the base for the opening move.
        # Note: Yes, currently only one 'closing' move exists, but I want this to be extensible :)
        move = fyc.closing_move_id.id
        closing_move=pool.get('account.move').browse(cr,uid,move)
        if operation == 'open':
            if not closing_move:
                raise osv.except_osv(_('UserError'), _("The closing move must exist to create the opening one"))
            if not closing_move.line_id:
                raise osv.except_osv(_('UserError'), _("The closing move shouldn't be empty"))
            # Get the values for the lines
            if not fyc.o_description:
                raise osv.except_osv(_('UserError'), _("The opening description must be defined"))
            if not fyc.o_date:
                raise osv.except_osv(_('UserError'), _("The opening date must be defined"))
            if not (fyc.o_period_id and fyc.o_period_id.id):
                raise osv.except_osv(_('UserError'), _("The opening period must be defined"))
            if not (fyc.o_journal_id and fyc.o_journal_id.id):
                raise osv.except_osv(_('UserError'), _("The opening journal must be defined"))
            description = fyc.o_description
            date = fyc.o_date
            period_id = fyc.o_period_id.id
            journal_id = fyc.o_journal_id.id
        else:
            assert operation in ('open'), "The operation must be a supported one"

        # Read the lines from the closing move, and append the inverse lines to the opening move lines.
        for line in closing_move.line_id:
            move_lines.append({
                    'account_id': line.account_id.id,
                    'debit': line.credit,
                    'credit': line.debit,
                    'name': description,
                    'date': date,
                    'period_id': period_id,
                    'journal_id': journal_id,
                    'partner_id': line.partner_id.id,
                })

        # Finally create the account move with all the lines (if needed)
        if len(move_lines):
            move_id = pool.get('account.move').create(cr, uid, {
                'line_id': map(lambda x: (0,0,x), move_lines),
                'ref': description,
                'date': date,
                'period_id': period_id,
                'journal_id': journal_id,
                }, context={})
        else:
            move_id = None

        # Save the reference to the created account move into the fyc object
        if operation == 'open':
            pool.get('l10n_es_fiscal_year_closing.fyc').write(cr, uid, [fyc.id], { 'opening_move_id': move_id })
        else:
            assert operation in ('open'), "The operation must be a supported one"
        return move_id
    
    def execute_run(self, cr, uid, data, context=None):
        """
        Creates / removes FYC entries
        """
        try:
            pool = pooler.get_pool(cr.dbname)

            #
            # If the wizard is in cancel mode, run the objects cancel action
            # to let it undo the confirmation action, before running the wizard.
            #
    
            # Read the object
            fyc = pool.get('l10n_es_fiscal_year_closing.fyc').browse(cr, uid, context['active_id'], context=context)

            #
            # Calculate the operations to perform (needed to calculate the progress)
            #
            total_operations = 0
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
                    self._check_invalid_period_moves(cr, uid, fyc, context)

                #
                # Check for draft moves if needed
                #
                if fyc.check_draft_moves:
                    self._check_draft_moves(cr, uid, fyc, context)

                #
                # Check for unbalanced moves if needed
                #
                if fyc.check_unbalanced_moves:
                    self._check_unbalanced_moves(cr, uid, fyc, context)

                #
                # Create L&P move if needed
                #
                if fyc.create_loss_and_profit and not fyc.loss_and_profit_move_id:
                    self.create_closing_move(cr, uid, 'loss_and_profit', fyc, context)

                #
                # Remove the L&P move if needed
                #
                if (not fyc.create_loss_and_profit) and fyc.loss_and_profit_move_id:
                    self.remove_move(cr, uid, 'loss_and_profit', fyc, context)

                # Refresh the cached fyc object
                fyc = pool.get('l10n_es_fiscal_year_closing.fyc').browse(cr, uid, fyc.id, context=context)

                #
                # Create the Net L&P move if needed
                #
                if fyc.create_net_loss_and_profit and not fyc.net_loss_and_profit_move_id:
                    self.create_closing_move(cr, uid, 'net_loss_and_profit', fyc, context)
                    
                #
                # Remove the Net L&P move if needed
                #
                if (not fyc.create_net_loss_and_profit) and fyc.net_loss_and_profit_move_id:
                    self.remove_move(cr, uid, 'net_loss_and_profit', fyc, context)

                #
                # Create the closing move if needed
                #
                if fyc.create_closing and not fyc.closing_move_id:
                    self.create_closing_move(cr, uid, 'close', fyc, context)

                #
                # Remove the closing move if needed
                #
                if (not fyc.create_closing) and fyc.closing_move_id:
                    self.remove_move(cr, uid, 'close', fyc, context)
                    #operations_done += 1

                # Refresh the cached fyc object
                fyc = pool.get('l10n_es_fiscal_year_closing.fyc').browse(cr, uid, fyc.id, context=context)
                #
                # Create the opening move if needed
                #
                if fyc.create_opening and not fyc.opening_move_id:
                    self.create_opening_move(cr, uid, 'open', fyc, context)
                #
                # Remove the opening move if needed
                #
                if (not fyc.create_opening) and fyc.opening_move_id:
                    self.remove_move(cr, uid, 'open', fyc, context)

            fyc = pool.get('l10n_es_fiscal_year_closing.fyc').browse(cr, uid, fyc.id, context=context)
            #
            # Set the as done (if not in cancel_mode)
            #
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'l10n_es_fiscal_year_closing.fyc', fyc.id, 'run', cr)

            cr.commit()
        except Exception:
            cr.rollback()
            raise
        return {'type': 'ir.actions.act_window_close'}

execute_fyc()
