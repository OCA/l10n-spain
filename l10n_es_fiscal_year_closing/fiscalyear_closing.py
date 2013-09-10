# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Pexego Sistemas Informáticos. All Rights Reserved
#    Copyright (c) 2013 Servicios Tecnológicos Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
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
##############################################################################
from openerp.osv import fields, orm
from openerp import netsvc
from openerp.tools.translate import _
from datetime import datetime
from tools import config
import logging


class fiscalyear_closing_account_mapping(orm.AbstractModel):
    _name = "account.fiscalyear.closing.account_map"
    _description = "Generic account mapping"

    _columns = {
        'name': fields.char('Description', size=60, required=False),
        'fyc_id': fields.many2one('account.fiscalyear.closing', 'Fiscal Year Closing', ondelete='cascade', required=True, select=1),
        'source_account_id':fields.many2one('account.account', 'Source account', required=True, ondelete='cascade'),
        'dest_account_id':fields.many2one('account.account', 'Dest account', required=False, ondelete='cascade'),
    }


class fiscalyear_closing_lp_account_mapping(orm.Model):
    _name = "account.fiscalyear.closing.lp_account_map"
    _inherit = "account.fiscalyear.closing.account_map"
    _description = "SFYC Loss & Profit Account Mapping"


class fiscalyear_closing_nlp_account_mapping(orm.Model):
    _name = "account.fiscalyear.closing.nlp_account_map"
    _inherit = "account.fiscalyear.closing.account_map"
    _description = "SFYC Net Loss & Profit Account Mapping"


class fiscalyear_closing_c_account_mapping(orm.Model):
    _name = "account.fiscalyear.closing.c_account_map"
    _inherit = "account.fiscalyear.closing.account_map"
    _description = "SFYC Closing Account Mapping"


class fiscalyear_closing(orm.Model):
    _name = "account.fiscalyear.closing"
    _description = "Fiscal year closing"

    _columns = {
        'name': fields.char('Description', size=60, required=True),
        'company_id': fields.many2one('res.company', 'Company', ondelete='cascade', readonly=True, required=True),
        # Fiscal years
        'closing_fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal year to close', required=True, ondelete='cascade', select=1),
        'opening_fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal year to open', required=True, ondelete='cascade', select=2),
        # Operations (to do), and their account moves (when done)
        'create_loss_and_profit': fields.boolean('Create Loss & Profit move'),
        'loss_and_profit_move_id': fields.many2one('account.move', 'L&P Move', ondelete='set null', readonly=True),
        'create_net_loss_and_profit': fields.boolean('Create Net Loss & Profit move'),
        'net_loss_and_profit_move_id': fields.many2one('account.move', 'Net L&P Move', ondelete='set null', readonly=True),
        'create_closing': fields.boolean('Create closing move'),
        'closing_move_id': fields.many2one('account.move', 'Closing Move', ondelete='set null', readonly=True),
        'create_opening': fields.boolean('Create opening move'),
        'opening_move_id': fields.many2one('account.move', 'Opening Move', ondelete='set null', readonly=True),
        # Extra operations
        'check_invalid_period_moves': fields.boolean('Check invalid period or date moves', help="Checks that there are no moves, on the fiscal year that is being closed, with dates or periods outside that fiscal year."),
        'check_draft_moves': fields.boolean('Check draft moves', help="Checks that there are no draft moves on the fiscal year that is being closed. Non-confirmed moves won't be taken in account on the closing operations."),
        'check_unbalanced_moves': fields.boolean('Check unbalanced moves', help="Checks that there are no unbalanced moves on the fiscal year that is being closed."),
        'state': fields.selection([
                ('new', 'New'),
                ('draft', 'Draft'),
                ('in_progress', 'In progress'),
                ('done', 'Done'),
                ('cancelled', 'Cancelled'),
            ], 'Status'),
        # Loss and Profit options
        'lp_description': fields.char('Description', size=60),
        'lp_journal_id': fields.many2one('account.journal', 'Journal'),
        'lp_period_id': fields.many2one('account.period', 'Period'),
        'lp_date': fields.date('Date'),
        'lp_account_mapping_ids': fields.one2many('account.fiscalyear.closing.lp_account_map', 'fyc_id', 'Account mappings'),
        # Net Loss and Profit options
        'nlp_description': fields.char('Description', size=60),
        'nlp_journal_id': fields.many2one('account.journal', 'Journal'),
        'nlp_period_id': fields.many2one('account.period', 'Period'),
        'nlp_date': fields.date('Date'),
        'nlp_account_mapping_ids': fields.one2many('account.fiscalyear.closing.nlp_account_map', 'fyc_id', 'Account mappings'),
        # Closing options
        'c_description': fields.char('Description', size=60),
        'c_journal_id': fields.many2one('account.journal', 'Journal'),
        'c_period_id': fields.many2one('account.period', 'Period'),
        'c_date': fields.date('Date'),
        'c_account_mapping_ids': fields.one2many('account.fiscalyear.closing.c_account_map', 'fyc_id', 'Accounts'),
        # Opening options
        'o_description': fields.char('Description', size=60),
        'o_journal_id': fields.many2one('account.journal', 'Journal'),
        'o_period_id': fields.many2one('account.period', 'Period'),
        'o_date': fields.date('Date'),
    }

    def _get_closing_fiscalyear_id(self, cr, uid, context):
        """
        Gets the last (previous) fiscal year
        """
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id
        fiscalyear_ids = self.pool.get('account.fiscalyear').search(cr, uid, [
                            ('company_id', '=', company_id), 
                            ('state', '=', 'draft'), 
                        ], order='date_start')
        return fiscalyear_ids and fiscalyear_ids[0]

    def _get_opening_fiscalyear_id(self, cr, uid, context):
        """
        Gets the current fiscal year
        """
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id
        closing_fy_id = self._get_closing_fiscalyear_id(cr, uid, context)
        closing_fy = fiscalyear_obj.read(cr, uid, closing_fy_id, ['date_stop'], context)
        fiscalyear_ids = fiscalyear_obj.search(cr, uid, [
                            ('company_id', '=', company_id),
                            ('date_start', '>', closing_fy['date_stop']),
                            ('state', '=', 'draft'),
                        ], order='date_start')
        return fiscalyear_ids and fiscalyear_ids[0]

    def _check_duplicate(self, cr, uid, ids, context=None):
        for fyc in self.browse(cr, uid, ids, context):
            if len(self.search(cr, uid, [('closing_fiscalyear_id', '=', 
                                          fyc.closing_fiscalyear_id.id)])) > 1:
                return False
            if len(self.search(cr, uid, [('opening_fiscalyear_id', '=', 
                                          fyc.opening_fiscalyear_id.id)])) > 1:
                return False
        return True

    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id,
        'state': lambda *a: 'new',
        'name': lambda self, cr, uid, context: _("%s Fiscal Year Closing") % (datetime.now().year - 1),
        'closing_fiscalyear_id': _get_closing_fiscalyear_id,
        'opening_fiscalyear_id': _get_opening_fiscalyear_id,
    }

    _constraints = [
        (_check_duplicate, _('There is already a fiscal year closing with the same opening or ending fiscal year.'), [])
    ]

    def unlink(self, cr, uid, ids, context=None):
        context = context or {}
        for fyc in self.read(cr, uid, ids, ['state'], context=context):
            if fyc['state'] in ('in_progress', 'done'):
                raise orm.except_orm(_('Error!'), _('You cannot delete a fiscal year closing which is in progress or done. You have to cancel it first.'))
        return super(fiscalyear_closing, self).unlink(cr, uid, ids, context=context)

    def _get_journal_id(self, cr, uid, fyc, context):
        """
        Gets the journal to use.
        (It will search for a 'GRAL' or 'General' journal)
        """
        journal_ids = self.pool.get('account.journal').search(cr, uid, [
                        ('company_id', '=', fyc.company_id.id),
                        ('type', '=', 'general'),
                    ])
        return journal_ids and journal_ids[0]

    def _get_lp_period_id(self, cr, uid, fyc, context):
        """
        Gets the period for the L&P entry
        (It searches for a "PG%" special period on the previous fiscal year)
        """
        period_ids = self.pool.get('account.period').search(cr, uid, [
                            ('fiscalyear_id', '=', fyc.closing_fiscalyear_id.id),
                            ('special', '=', True),
                            ('date_start', '=', fyc.closing_fiscalyear_id.date_stop),
                            ('code', 'ilike', 'PG'),
                        ])
        if not period_ids:
            period_ids = self.pool.get('account.period').search(cr, uid, [
                                ('fiscalyear_id', '=', fyc.closing_fiscalyear_id.id),
                                ('special', '=', True),
                                ('date_start', '=', fyc.closing_fiscalyear_id.date_stop),
                            ])
        return period_ids and period_ids[0]

    def _get_c_period_id(self, cr, uid, fyc, context):
        """
        Gets the period for the Closing entry
        (It searches for a "C%" special period on the previous fiscal year)
        """
        period_ids = self.pool.get('account.period').search(cr, uid, [
                            ('fiscalyear_id', '=', fyc.closing_fiscalyear_id.id),
                            ('special', '=', True),
                            ('date_start', '=', fyc.closing_fiscalyear_id.date_stop),
                            ('code', 'ilike', 'C'),
                        ])

        if not period_ids:
            period_ids = self.pool.get('account.period').search(cr, uid, [
                                ('fiscalyear_id', '=', fyc.closing_fiscalyear_id.id),
                                ('special', '=', True),
                                ('date_start', '=', fyc.closing_fiscalyear_id.date_stop),
                            ])
        return period_ids and period_ids[0]

    def _get_o_period_id(self, cr, uid, fyc, context):
        """
        Gets the period for the Opening entry
        (It searches for a "A%" special period on the previous fiscal year)
        """
        period_ids = self.pool.get('account.period').search(cr, uid, [
                            ('fiscalyear_id', '=', fyc.opening_fiscalyear_id.id),
                            ('special', '=', True),
                            ('date_stop', '=', fyc.opening_fiscalyear_id.date_start),
                            ('code', 'ilike', 'A'),
                        ])
        if not period_ids:
            period_ids = self.pool.get('account.period').search(cr, uid, [
                                ('fiscalyear_id', '=', fyc.opening_fiscalyear_id.id),
                                ('special', '=', True),
                                ('date_stop', '=', fyc.opening_fiscalyear_id.date_start),
                            ])
        return period_ids and period_ids[0]

    def _get_lp_account_mapping(self, cr, uid, fyc, context=None):
        return []

    def _get_nlp_account_mapping(self, cr, uid, fyc, context=None):
        return []

    def _get_c_account_mapping(self, cr, uid, fyc, context=None):
        return []

    def _get_defaults(self, cr, uid, fyc, context=None):
        context = context or {}
        vals = {
            'create_loss_and_profit': True,
            'create_net_loss_and_profit': False,
            'create_closing': True,
            'create_opening': True,
            'check_invalid_period_moves': True,
            'check_draft_moves': True,
            'check_unbalanced_moves': True,
            # L&P options
            'lp_description': _("Loss & Profit"),
            'lp_journal_id': self._get_journal_id(cr, uid, fyc, context),
            'lp_period_id': self._get_lp_period_id(cr, uid, fyc, context),
            'lp_date': fyc.closing_fiscalyear_id.date_stop,
            'lp_account_mapping_ids': self._get_lp_account_mapping(cr, uid, fyc, context),
            # Net L&P options
            'nlp_description': _("Net Loss & Profit"),
            'nlp_journal_id': self._get_journal_id(cr, uid, fyc, context),
            'nlp_period_id': self._get_lp_period_id(cr, uid, fyc, context),
            'nlp_date': fyc.closing_fiscalyear_id.date_stop,
            'nlp_account_mapping_ids': self._get_nlp_account_mapping(cr, uid, fyc, context),
            # Closing options
            'c_description': _("Fiscal Year Closing"),
            'c_journal_id': self._get_journal_id(cr, uid, fyc, context),
            'c_period_id': self._get_c_period_id(cr, uid, fyc, context),
            'c_date': fyc.closing_fiscalyear_id.date_stop,
            'c_account_mapping_ids': self._get_c_account_mapping(cr, uid, fyc, context),
            # Opening options
            'o_description': _("Fiscal Year Opening"),
            'o_journal_id': self._get_journal_id(cr, uid, fyc, context),
            'o_period_id': self._get_o_period_id(cr, uid, fyc, context),
            'o_date': fyc.opening_fiscalyear_id.date_start,
            'state': 'draft',
        }
        return vals

#
# Workflow actions ---------------------------------------------------------
#

    def action_draft(self, cr, uid, ids, context=None):
        """
        Called when the user clicks the confirm button.
        """
        context = context or {}
        for fyc in self.browse(cr, uid, ids, context):
            # Check whether the default values of the fyc object have to be computed
            # or they have already been computed (restarted workflow)
            if fyc.c_account_mapping_ids:
                # Fyc wizard reverted to 'new' after cancelled
                self.write(cr, uid, [fyc.id], { 'state': 'draft' })
            else:
                # New fyc wizard object
                vals = self._get_defaults(cr, uid, fyc, context=context)
                self.write(cr, uid, [fyc.id], vals)
        return True

    def action_run(self, cr, uid, ids, context=None):
        """
        Called when the create entries button is used.
        """
        # Note: Just change the state, everything else is done on the run wizard
        #       *before* this action is called.
        self.write(cr, uid, ids, {'state': 'in_progress'})
        return True

    def action_confirm(self, cr, uid, ids, context=None):
        """
        Called when the user clicks the confirm button.
        """
        context = context or {}
        logger = logging.getLogger('l10n_es_fiscal_year_closing')
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        tmp_context = context.copy()
        tmp_context['fy_closing'] = True # Fiscal year closing = reconcile everything
        for fyc in self.browse(cr, uid, ids, context):
            # Require the L&P, closing, and opening moves to exist (NL&P is optional)
            if not fyc.loss_and_profit_move_id:
                raise orm.except_orm(_("Not all the operations have been performed!"), _("The Loss & Profit move is required"))
            if not fyc.closing_move_id:
                raise orm.except_orm(_("Not all the operations have been performed!"), _("The Closing move is required"))
            if not fyc.opening_move_id:
                raise orm.except_orm(_("Not all the operations have been performed!"), _("The Opening move is required"))
            # Calculate the moves to check
            moves = []
            moves.append(fyc.loss_and_profit_move_id)
            if fyc.net_loss_and_profit_move_id:
                moves.append(fyc.net_loss_and_profit_move_id)
            moves.append(fyc.closing_move_id)
            moves.append(fyc.opening_move_id)
            # Check and reconcile each of the moves
            for move in moves:
                logger.debug("Checking %s" % move.ref)
                # Check if it has been confirmed
                if move.state == 'draft':
                    raise orm.except_orm(_("Some moves are in draft state!"), _("You have to review and confirm each of the moves before continuing"))
                # Check the balance
                amount = 0
                for line in move.line_id:
                    amount += (line.debit - line.credit)
                if abs(amount) > 0.5 * 10 ** -int(precision):
                    raise orm.except_orm(_("Some moves are unbalanced!"), _("All the moves should be balanced before continuing"))
                # Reconcile the move
                # Note: We will reconcile all the lines, even the 'not reconcile' ones,
                #       to prevent future problems (the user may change the
                #       reconcile option of an account in the future)
                logger.debug("Reconcile %s" % move.ref)
                line_ids = [line.id for line in move.line_id]
                r_id = self.pool.get('account.move.reconcile').create(cr, uid, 
                    {'type': 'auto', 
                     'opening_reconciliation': True,
                     })
                cr.execute("""UPDATE account_move_line 
                    SET reconcile_id = %s 
                    WHERE id in %s""",
                    (r_id, tuple(line_ids),))
            # Close the fiscal year and it's periods
            # Note: We can not just do a write, cause it would raise a
            #       "You can not modify/delete a journal with entries for this period!"
            #       so we have to do it on SQL level :(
            #       This is based on the "account.fiscalyear.close.state" wizard.
            logger.debug("Closing fiscal year")
            fy_id = fyc.closing_fiscalyear_id.id
            cr.execute('UPDATE account_journal_period ' \
                        'SET state = %s ' \
                        'WHERE period_id IN (SELECT id FROM account_period \
                        WHERE fiscalyear_id = %s)',
                    ('done', fy_id))
            cr.execute('UPDATE account_period SET state = %s ' \
                    'WHERE fiscalyear_id = %s', ('done', fy_id))
            cr.execute('UPDATE account_fiscalyear ' \
                    'SET state = %s WHERE id = %s', ('done', fy_id))
        self.write(cr, uid, ids, {'state': 'done'})
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        """
        Called when the user clicks the cancel button.
        """
        context = context or {}
        self.write(cr, uid, ids, {'state': 'cancelled'})
        return True

    def action_recover(self, cr, uid, ids, context=None):
        """
        Called when the user clicks the draft button to create
        a new workflow instance.
        """
        wf_service = netsvc.LocalService("workflow")
        for item_id in ids:
            wf_service.trg_delete(uid, 'account.fiscalyear.closing', item_id, cr)
            wf_service.trg_create(uid, 'account.fiscalyear.closing', item_id, cr)
            wf_service.trg_validate(uid, 'account.fiscalyear.closing', item_id, 'draft', cr)
        return True
