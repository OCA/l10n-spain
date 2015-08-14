# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP - Import operations model 347 engine
#    Copyright (C) 2009 Asr Oss. All Rights Reserved
#    Copyright (c) 2012 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2012 Avanzosc (http://www.avanzosc.com)
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
#############################################################################

from openerp import netsvc
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp.tools import float_is_zero


class CancelFyc(orm.TransientModel):

    _name = "account.fiscalyear.closing.cancel_wizard"
    _description = "Cancel the Fiscal Year Closing"
    _columns = {
        'delete_pyg': fields.boolean(
            'Delete P&L account move', readonly=True),
        'delete_net_pyg': fields.boolean(
            'Delete net P&L account move', readonly=True),
        'delete_close': fields.boolean(
            'Delete closing account move', readonly=True),
        'delete_open': fields.boolean(
            'Delete opening account move', readonly=True),
    }

    def default_get(self, cr, uid, field_list, context=None):
        """This function gets default values
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param fields: List of fields for default value
        @param context: A standard dictionary for contextual values

        @return : default values of fields.
        """
        if context is None:
            context = {}
        res = super(CancelFyc, self).default_get(cr, uid, field_list,
                                                 context=context)
        if context.get('active_id'):
            fyc = self.pool['account.fiscalyear.closing'].browse(
                cr, uid, context['active_id'])
            res['delete_pyg'] = bool(fyc.loss_and_profit_move_id)
            res['delete_net_pyg'] = bool(fyc.net_loss_and_profit_move_id)
            res['delete_close'] = bool(fyc.closing_move_id)
            res['delete_open'] = bool(fyc.opening_move_id)
        return res

    def _remove_move(self, cr, uid, move, context):
        """Remove an account move, removing reconciles if any"""
        # Unreconcile the move if needed
        reconcile_ids = set()
        for line in move.line_id:
            if line.reconcile_id:
                reconcile_ids.add(line.reconcile_id.id)
            elif line.reconcile_partial_id:
                reconcile_ids.add(line.reconcile_partial_id.id)
        reconcile_ids = list(reconcile_ids)
        if reconcile_ids:
            # Call base method to avoid checks, but to not bypass ORM
            osv.osv.unlink(self.pool.get('account.move.reconcile'),
                           cr, uid, reconcile_ids, context=context)

        obj_move = self.pool.get('account.move')
        # Remove the move after changing it's state to draft
        obj_move.write(cr, uid, [move.id], {'state': 'draft'}, context)
        # Done in this way for performance reasons instead of letting
        # move unlink code to act
        line_ids = map(lambda x: x.id, move.line_id)
        self.pool.get('account.move.line').unlink(cr, uid, line_ids,
                                                  context=context, check=False)
        obj_move.unlink(cr, uid, [move.id], context)

        return move.id

    def run_cancel(self, cr, uid, data, context=None):
        fyc_obj = self.pool.get('account.fiscalyear.closing')
        fyc = fyc_obj.browse(cr, uid, context['active_id'], context=context)
        fy_id = fyc.closing_fiscalyear_id.id
        # Open the fiscal year and it's periods
        cr.execute('UPDATE account_journal_period '
                   'SET state = %s '
                   'WHERE period_id IN (SELECT id FROM account_period '
                   'WHERE fiscalyear_id = %s)',
                   ('draft', fy_id))
        cr.execute('UPDATE account_period SET state = %s '
                   'WHERE fiscalyear_id = %s',
                   ('draft', fy_id))
        cr.execute('UPDATE account_fiscalyear '
                   'SET state = %s WHERE id = %s',
                   ('draft', fy_id))
        result = {}
        if fyc.loss_and_profit_move_id or fyc.net_loss_and_profit_move_id or \
                fyc.closing_move_id or fyc.opening_move_id:
            if fyc.loss_and_profit_move_id:
                self._remove_move(cr, uid, fyc.loss_and_profit_move_id,
                                  context)
                result['loss_and_profit_move_id'] = False
            if fyc.net_loss_and_profit_move_id:
                self._remove_move(cr, uid, fyc.net_loss_and_profit_move_id,
                                  context)
                result['net_loss_and_profit_move_id'] = False
            if fyc.closing_move_id:
                self._remove_move(cr, uid, fyc.closing_move_id, context)
                result['closing_move_id'] = False
            if fyc.opening_move_id:
                self._remove_move(cr, uid, fyc.opening_move_id, context)
                result['opening_move_id'] = False
        fyc_obj.write(cr, uid, [fyc.id], result, context)
        # Change workflow state
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'account.fiscalyear.closing',
                                context['active_id'], 'cancel', cr)
        return {'type': 'ir.actions.act_window_close'}


class ExecuteFyc(orm.TransientModel):
    _name = 'account.fiscalyear.closing.execute_wizard'
    _description = "Execute the Fiscal Year Closing"

    _columns = {
        'create_pyg': fields.boolean('Create P&L move', readonly=True),
        'create_net_pyg': fields.boolean('Create Net P&L move', readonly=True),
        'create_close': fields.boolean('Create closing move', readonly=True),
        'create_open': fields.boolean('Create opening move', readonly=True),
        'check_draft': fields.boolean('Check draft moves', readonly=True),
        'check_unbalanced': fields.boolean('Check unbalanced moves',
                                           readonly=True),
        'check_invalid': fields.boolean('Check invalid periods or date moves',
                                        readonly=True),
    }

    def default_get(self, cr, uid, field_list, context=None):
        """This function gets default values
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param fields: List of fields for default value
        @param context: A standard dictionary for contextual values

        @return : default values of fields.
        """
        if context is None:
            context = {}
        res = super(ExecuteFyc, self).default_get(cr, uid, field_list,
                                                  context=context)
        if context.get('active_id'):
            fyc = self.pool['account.fiscalyear.closing'].browse(
                cr, uid, context['active_id'])
            res['create_pyg'] = fyc.create_loss_and_profit
            res['create_net_pyg'] = fyc.create_net_loss_and_profit
            res['create_close'] = fyc.create_closing
            res['create_open'] = fyc.create_opening
            res['check_draft'] = fyc.check_draft_moves
            res['check_unbalanced'] = fyc.check_unbalanced_moves
            res['check_invalid'] = fyc.check_invalid_period_moves
        return res

    def _check_invalid_period_moves(self, cr, uid, fyc, context):
        """Checks for moves with invalid period on the fiscal year that is
        being closed
        """
        move_obj = self.pool.get('account.move')
        # Consider all the periods of the fiscal year.
        period_ids = [period.id for period in
                      fyc.closing_fiscalyear_id.period_ids]
        # Find moves on the closing fiscal year with dates of previous years
        account_move_ids = move_obj.search(cr, uid, [
            ('period_id', 'in', period_ids),
            ('date', '<', fyc.closing_fiscalyear_id.date_start),
        ], context=context)
        # Find moves on the closing fiscal year with dates of next years
        account_move_ids.extend(move_obj.search(cr, uid, [
            ('period_id', 'in', period_ids),
            ('date', '>', fyc.closing_fiscalyear_id.date_stop),
        ], context=context))
        # Find moves not on the closing fiscal year with dates on its year
        account_move_ids.extend(move_obj.search(cr, uid, [
            ('period_id', 'not in', period_ids),
            ('date', '>=', fyc.closing_fiscalyear_id.date_start),
            ('date', '<=', fyc.closing_fiscalyear_id.date_stop),
        ], context=context))
        # If one or more moves where found, raise an exception
        if len(account_move_ids):
            invalid_period_moves = move_obj.browse(cr, uid, account_move_ids,
                                                   context)
            str_invalid_period_moves = '\n'.join(
                [
                    'id: %s, date: %s, number: %s, ref: %s' %
                    (move.id, move.date, move.name, move.ref) for move in
                    invalid_period_moves
                ]
            )
            raise orm.except_orm(
                _('Error'),
                _('One or more moves with invalid period or date found on the '
                  'fiscal year: \n%s')
                % str_invalid_period_moves)

    def _check_draft_moves(self, cr, uid, fyc, context):
        """Checks for draft moves on the fiscal year that is being closed"""
        move_obj = self.pool['account.move']
        # Consider all the periods of the fiscal year *BUT* the L&P, Net L&P
        # and the closing one.
        period_ids = []
        for period in fyc.closing_fiscalyear_id.period_ids:
            if period.id != fyc.lp_period_id.id \
                    and period.id != fyc.nlp_period_id.id \
                    and period.id != fyc.c_period_id.id:
                period_ids.append(period.id)
        draft_move_ids = move_obj.search(cr, uid,
                                         [('period_id', 'in', period_ids),
                                          ('state', '=', 'draft')],
                                         context=context)
        # If one or more draft moves where found, raise an exception
        if draft_move_ids:
            str_draft_moves = ''
            for move in move_obj.browse(cr, uid, draft_move_ids,
                                        context=context):
                str_draft_moves += ('id: %s, date: %s, number: %s, ref: %s\n'
                                    % (move.id, move.date, move.name,
                                       move.ref))
            raise orm.except_orm(
                _('Error'),
                _('One or more draft moves found: \n%s') % str_draft_moves
            )

    def _check_unbalanced_moves(self, cr, uid, fyc, context):
        """Checks for unbalanced moves on the fiscal year that is being
        closed"""
        move_obj = self.pool['account.move']
        decimal_precision_obj = self.pool['decimal.precision']
        # Consider all the periods of the fiscal year *BUT* the L&P, Net L&P
        # and the Closing one.
        period_ids = []
        for period in fyc.closing_fiscalyear_id.period_ids:
            if period.id != fyc.lp_period_id.id \
                    and period.id != fyc.nlp_period_id.id \
                    and period.id != fyc.c_period_id.id:
                period_ids.append(period.id)
        # Find the moves on the given periods
        account_move_ids = move_obj.search(cr, uid, [
            ('period_id', 'in', period_ids),
            ('state', '!=', 'draft'),
        ], context=context)
        # For each found move, check it
        unbalanced_moves = []
        for move in move_obj.browse(cr, uid, account_move_ids, context):
            amount = 0
            for line in move.line_id:
                amount += (line.debit - line.credit)
            if round(abs(amount), decimal_precision_obj.precision_get(
                    cr, uid, 'Account')) > 0:
                unbalanced_moves.append(move)
        # If one or more unbalanced moves where found, raise an exception
        if len(unbalanced_moves):
            str_unbalanced_moves = '\n'.join(
                [
                    'id: %s, date: %s, number: %s, ref: %s'
                    % (move.id, move.date, move.name, move.ref) for move in
                    unbalanced_moves
                ]
            )
            raise orm.except_orm(
                _('Error'),
                _('One or more unbalanced moves found: \n%s') %
                str_unbalanced_moves)

    def _create_closing_move(self, cr, uid, account_mapping_ids, period_ids,
                             description, date, period_id, journal_id,
                             company_id, fiscalyear_id, context=None):
        """Create a closing move with the given data, provided by another
        method.
        """
        if context is None:
            context = {}
        move_lines = []
        dest_accounts_totals = {}
        ctx = context.copy()
        ctx.update({'fiscalyear': fiscalyear_id,
                    'periods': period_ids,
                    'company_id': company_id})
        account_obj = self.pool['account.account']
        move_line_obj = self.pool['account.move.line']
        decimal_precision_obj = self.pool['decimal.precision']
        precision = decimal_precision_obj.precision_get(cr, uid, 'Account')
        # For each (parent) account in the mapping list
        for account_map in account_mapping_ids:
            # Init (if needed) the dictionary that will store the totals for
            # the dest accounts
            if account_map.dest_account_id and not \
                    dest_accounts_totals.get(account_map.dest_account_id.id):
                dest_accounts_totals[account_map.dest_account_id.id] = 0
            # Find its children accounts (recursively)
            # FIXME: _get_children_and_consol is a protected member of
            # account_account,
            # but the OpenERP code base uses it like this :(
            child_ids = account_obj._get_children_and_consol(
                cr, uid, [account_map.source_account_id.id], ctx)
            # For each children account. (Notice the context filter! the
            # computed balanced is based on this filter)
            for account in account_obj.browse(cr, uid, child_ids, ctx):
                # Check if the children account needs to (and can) be closed
                if account.type == 'view':
                    continue
                if account.user_type.close_method == 'balance':
                    # Compute the balance for the account (uses the
                    # previous browse context filter)
                    balance = account.balance
                    # Check if the balance is greater than the limit
                    if not float_is_zero(
                            balance, precision_digits=precision):
                        # Add a new line to the move
                        move_lines.append({
                            'account_id': account.id,
                            'debit': balance < 0 and -balance,
                            'credit': balance > 0 and balance,
                            'name': description,
                            'date': date,
                            'partner_id': False,
                            'period_id': period_id,
                            'journal_id': journal_id,
                        })
                        # Update the dest account total (with the inverse
                        # of the balance)
                        if account_map.dest_account_id:
                            dest_id = account_map.dest_account_id.id
                            dest_accounts_totals[dest_id] -= balance
                elif account.user_type.close_method == 'unreconciled':
                    found_lines = move_line_obj.search(cr, uid, [
                        ('period_id', 'in', period_ids),
                        ('account_id', '=', account.id),
                        ('company_id', '=', company_id),
                    ])
                    lines_by_partner = {}
                    for line in move_line_obj.browse(cr, uid, found_lines):
                        partner_id = line.partner_id.id
                        balance = line.debit - line.credit
                        lines_by_partner[partner_id] = (
                            lines_by_partner.get(partner_id, 0.0) + balance)
                    for partner_id in lines_by_partner.keys():
                        balance = lines_by_partner[partner_id]
                        if not float_is_zero(
                                balance, precision_digits=precision):
                            move_lines.append({
                                'account_id': account.id,
                                'debit': balance < 0 and -balance,
                                'credit': balance > 0 and balance,
                                'name': description,
                                'date': date,
                                'period_id': period_id,
                                'journal_id': journal_id,
                                'partner_id': partner_id,
                            })
                        # Update the dest account total (with the inverse
                        # of the balance)
                        if account_map.dest_account_id:
                            dest_id = account_map.dest_account_id.id
                            dest_accounts_totals[dest_id] -= balance
                elif account.user_type.close_method == 'detail':
                    raise orm.except_orm(
                        _('UserError'),
                        _("Account type closing method is not supported"))
                else:
                    # Account type has no closing method or method is not
                    # listed
                    continue
        # Add the dest lines
        for dest_account_id in dest_accounts_totals.keys():
            balance = dest_accounts_totals[dest_account_id]
            move_lines.append({
                'account_id': dest_account_id,
                'debit': balance < 0 and -balance,
                'credit': balance > 0 and balance,
                'name': description,
                'date': date,
                'partner_id': False,
                'period_id': period_id,
                'journal_id': journal_id,
            })
        # Finally create the account move with all the lines (if needed)
        if len(move_lines):
            move_id = self.pool.get('account.move').create(cr, uid, {
                'line_id': map(lambda x: (0, 0, x), move_lines),
                'ref': description,
                'date': date,
                'period_id': period_id,
                'journal_id': journal_id,
            }, context={})
        else:
            move_id = False
        return move_id

    def create_closing_move(self, cr, uid, operation, fyc, context):
        """Create a closing move (L&P, NL&P or Closing move)."""
        period_ids = []
        account_mapping_ids = []

        # Depending on the operation we will use different data
        assert operation in ('loss_and_profit', 'net_loss_and_profit',
                             'close'), \
            (_("The operation must be a supported one"))
        if operation == 'loss_and_profit':
            # Consider all the periods of the fiscal year *BUT* the L&P, Net
            # L&P and the Closing one.
            for period in fyc.closing_fiscalyear_id.period_ids:
                if period.id != fyc.lp_period_id.id \
                        and period.id != fyc.nlp_period_id.id \
                        and period.id != fyc.c_period_id.id:
                    period_ids.append(period.id)
            # Set the accounts to use
            account_mapping_ids = fyc.lp_account_mapping_ids
            for account_map in account_mapping_ids:
                if not account_map.dest_account_id:
                    raise orm.except_orm(
                        _('UserError'),
                        _("The L&P account mappings are not properly "
                          "configured: %s") % account_map.name
                    )
            # Get the values for the lines
            description = fyc.lp_description
            date = fyc.lp_date
            period_id = fyc.lp_period_id.id
            journal_id = fyc.lp_journal_id.id
        elif operation == 'net_loss_and_profit':
            # Consider all the periods of the fiscal year *BUT* the Net L&P
            # and the Closing one.
            for period in fyc.closing_fiscalyear_id.period_ids:
                if period.id != fyc.nlp_period_id.id \
                        and period.id != fyc.c_period_id.id:
                    period_ids.append(period.id)
            # Set the accounts to use
            account_mapping_ids = fyc.nlp_account_mapping_ids
            for account_map in account_mapping_ids:
                if not account_map.dest_account_id:
                    raise orm.except_orm(
                        _('UserError'),
                        _("The Net L&P account mappings are not properly "
                          "configured: %s") % account_map.name
                    )
            # Get the values for the lines
            description = fyc.nlp_description
            date = fyc.nlp_date
            period_id = fyc.nlp_period_id.id
            journal_id = fyc.nlp_journal_id.id
        elif operation == 'close':
            # Require the user to have performed the L&P operation
            if not fyc.loss_and_profit_move_id:
                raise orm.except_orm(
                    _('UserError'),
                    _("The L&P move must exist before creating the closing "
                      "one"))
            # Consider all the periods of the fiscal year *BUT* the closing
            # one.
            for period in fyc.closing_fiscalyear_id.period_ids:
                if period.id != fyc.c_period_id.id:
                    period_ids.append(period.id)
            # Set the accounts to use
            account_mapping_ids = fyc.c_account_mapping_ids
            # Get the values for the lines
            description = fyc.c_description
            date = fyc.c_date
            period_id = fyc.c_period_id.id
            journal_id = fyc.c_journal_id.id

        return self._create_closing_move(
            cr, uid, account_mapping_ids,
            period_ids, description, date, period_id, journal_id,
            fyc.company_id.id, fyc.closing_fiscalyear_id.id, context
        )

    def create_opening_move(self, cr, uid, operation, fyc, context):
        """
        Create an opening move (based on the closing one)
        """
        move_obj = self.pool.get('account.move')
        closing_move = move_obj.browse(cr, uid, fyc.closing_move_id.id)
        if operation == 'open':
            if not closing_move:
                raise orm.except_orm(
                    _('UserError'),
                    _("The closing move must exist to create the opening one"))
            if not closing_move.line_id:
                raise orm.except_orm(_('UserError'),
                                     _("The closing move shouldn't be empty"))
            # Get the values for the lines
            description = fyc.o_description
            date = fyc.o_date
            period_id = fyc.o_period_id.id
            journal_id = fyc.o_journal_id.id
        else:
            assert operation in ('open'), \
                "The operation must be a supported one"
        # Read the lines from the closing move, and append the inverse lines to
        # the opening move lines.
        move_lines = []
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
            move_id = move_obj.create(cr, uid, {
                'line_id': map(lambda x: (0, 0, x), move_lines),
                'ref': description,
                'date': date,
                'period_id': period_id,
                'journal_id': journal_id,
            }, context={})
        else:
            move_id = False
        return move_id

    def run_execute(self, cr, uid, data, context=None):
        """Creates / removes FYC entries"""
        fyc_object = self.pool['account.fiscalyear.closing']
        fyc = fyc_object.browse(cr, uid, context['active_id'], context=context)
        if fyc.check_invalid_period_moves:
            self._check_invalid_period_moves(cr, uid, fyc, context)
        if fyc.check_draft_moves:
            self._check_draft_moves(cr, uid, fyc, context)
        if fyc.check_unbalanced_moves:
            self._check_unbalanced_moves(cr, uid, fyc, context)
        if fyc.create_loss_and_profit:
            move_id = self.create_closing_move(cr, uid, 'loss_and_profit', fyc,
                                               context)
            fyc_object.write(cr, uid, [fyc.id],
                             {'loss_and_profit_move_id': move_id})
        if fyc.create_net_loss_and_profit:
            move_id = self.create_closing_move(cr, uid, 'net_loss_and_profit',
                                               fyc, context)
            fyc_object.write(cr, uid, [fyc.id],
                             {'net_loss_and_profit_move_id': move_id})
        # Refresh content
        fyc = fyc_object.browse(cr, uid, fyc.id, context=context)
        if fyc.create_closing:
            move_id = self.create_closing_move(cr, uid, 'close', fyc, context)
            fyc_object.write(cr, uid, [fyc.id], {'closing_move_id': move_id})
            # Refresh content
            fyc = fyc_object.browse(cr, uid, fyc.id, context=context)
        if fyc.create_opening:
            move_id = self.create_opening_move(cr, uid, 'open', fyc, context)
            fyc_object.write(cr, uid, [fyc.id], {'opening_move_id': move_id})

        # Set the as done (if not in cancel_mode)
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'account.fiscalyear.closing', fyc.id,
                                'run', cr)
        return {'type': 'ir.actions.act_window_close'}
