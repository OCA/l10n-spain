# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account balance reporting engine
#    Copyright (C) 2009 Pexego Sistemas Informáticos.
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
Account balance report objects

Generic account balance report document (with header and detail lines).
Designed following the needs of the
Spanish/Spain localization.
"""
from openerp.osv import orm, fields
from openerp.tools.translate import _
import re
import time
from openerp import netsvc
import logging

# CSS classes for the account line templates
CSS_CLASSES = [('default', 'Default'), ('l1', 'Level 1'), ('l2', 'Level 2'),
               ('l3', 'Level 3'), ('l4', 'Level 4'), ('l5', 'Level 5')]


class AccountBalanceReporting(orm.Model):
    """Account balance report.
    It stores the configuration/header fields of an account balance report,
    and the linked lines of detail with the values of the accounting concepts
    (values generated from the selected template lines of detail formulas).
    """
    _name = "account.balance.reporting"

    READONLY_STATES = {'calc_done': [('readonly', True)],
                       'done': [('readonly', True)]}

    def _get_levels(self, cr, uid, context=None):
        cr.execute("select distinct level from account_account order by level")
        reg = cr.fetchall()
        res = [(str(x[0]), str(x[0])) for x in reg if x[0]]
        return res

    _columns = {
        'name': fields.char('Name', size=64, required=True, select=True),
        'template_id': fields.many2one(
            'account.balance.reporting.template',
            'Template', ondelete='set null', required=True, select=True,
            states=READONLY_STATES),
        'calc_date': fields.datetime("Calculation date", readonly=True),
        'state': fields.selection([('draft', 'Draft'),
                                   ('calc', 'Processing'),
                                   ('calc_done', 'Processed'),
                                   ('done', 'Done'),
                                   ('canceled', 'Canceled')], 'State'),
        'company_id': fields.many2one(
            'res.company', 'Company',
            ondelete='cascade', required=True, readonly=True,
            states=READONLY_STATES),
        'check_filter': fields.selection([('periods', 'Periods'),
                                          ('dates', 'Dates')],
                                         string='Compute by',
                                         required=True,
                                         states=READONLY_STATES),
        'level': fields.selection(_get_levels, string='Level',
                                  states=READONLY_STATES),
        'current_fiscalyear_id': fields.many2one(
            'account.fiscalyear',
            'Fiscal year 1', select=True, required=True,
            states={'calc_done': [('readonly', True)],
                    'done': [('readonly', True)]}),
        'current_period_ids': fields.many2many(
            'account.period',
            'account_balance_reporting_account_period_current_rel',
            'account_balance_reporting_id', 'period_id',
            'Fiscal year 1 periods',
            states={'calc_done': [('readonly', True)],
                    'done': [('readonly', True)]}),
        'current_date_from': fields.date('Date From', states=READONLY_STATES),
        'current_date_to': fields.date('Date To', states=READONLY_STATES),
        'previous_fiscalyear_id': fields.many2one(
            'account.fiscalyear',
            'Fiscal year 2', select=True,
            states={'calc_done': [('readonly', True)],
                    'done': [('readonly', True)]}),
        'previous_period_ids': fields.many2many(
            'account.period',
            'account_balance_reporting_account_period_previous_rel',
            'account_balance_reporting_id', 'period_id',
            'Fiscal year 2 periods',
            states={'calc_done': [('readonly', True)],
                    'done': [('readonly', True)]}),
        'previous_date_from': fields.date('Date From', states=READONLY_STATES),
        'previous_date_to': fields.date('Date To', states=READONLY_STATES),

        'line_ids': fields.one2many('account.balance.reporting.line',
                                    'report_id', 'Lines',
                                    states={'done': [('readonly', True)]}),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, context:
        self.pool['res.users'].browse(cr, uid, uid, context).company_id.id,
        'state': 'draft',
        'check_filter': 'periods',
    }

    def action_calculate(self, cr, uid, ids, context=None):
        """Called when the user presses the Calculate button.
        It will use the report template to generate lines of detail for the
        report with calculated values."""
        if context is None:
            context = {}
        line_obj = self.pool['account.balance.reporting.line']
        # Set the state to 'calculating'
        self.write(cr, uid, ids, {
            'state': 'calc',
            'calc_date': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        for report in self.browse(cr, uid, ids, context=context):
            # Clear the report data (unlink the lines of detail)
            line_obj.unlink(cr, uid, [line.id for line in report.line_ids],
                            context=context)
            # Fill the report with a 'copy' of the lines of its template
            # (if it has one)
            if report.template_id:
                for template_line in report.template_id.line_ids:
                    line_obj.create(cr, uid, {
                        'code': template_line.code,
                        'name': template_line.name,
                        'report_id': report.id,
                        'template_line_id': template_line.id,
                        'parent_id': None,
                        'current_value': None,
                        'previous_value': None,
                        'sequence': template_line.sequence,
                        'css_class': template_line.css_class,
                    }, context=context)
        # Set the parents of the lines in the report
        # Note: We reload the reports objects to refresh the lines of detail.
        for report in self.browse(cr, uid, ids, context=context):
            if report.template_id:
                # Set line parents (now that they have been created)
                for line in report.line_ids:
                    tmpl_line = line.template_line_id
                    if tmpl_line and tmpl_line.parent_id:
                        parent_line_ids = line_obj.search(
                            cr, uid, [('report_id', '=', report.id),
                                      ('code', '=', tmpl_line.parent_id.code)])
                        line_obj.write(cr, uid, line.id, {
                            'parent_id': (parent_line_ids and
                                          parent_line_ids[0] or False),
                        }, context=context)
        # Calculate the values of the lines
        # Note: We reload the reports objects to refresh the lines of detail.
        for report in self.browse(cr, uid, ids, context=context):
            if report.template_id:
                # Refresh the report's lines values
                for line in report.line_ids:
                    line.refresh_values()
                # Set the report as calculated
                self.write(cr, uid, [report.id], {
                    'state': 'calc_done'
                }, context=context)
            else:
                # Ouch! no template: Going back to draft state.
                self.write(cr, uid, [report.id], {'state': 'draft'},
                           context=context)
        return True

    def action_confirm(self, cr, uid, ids, context=None):
        """Called when the user clicks the confirm button."""
        self.write(cr, uid, ids, {'state': 'done'}, context=context)
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        """Called when the user clicks the cancel button."""
        self.write(cr, uid, ids, {'state': 'canceled'}, context=context)
        return True

    def action_recover(self, cr, uid, ids, context=None):
        """Called when the user clicks the draft button to create
        a new workflow instance."""
        self.write(cr, uid, ids, {'state': 'draft', 'calc_date': None},
                   context=context)
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_create(uid, 'account.balance.reporting', id, cr)
        return True

    def calculate_action(self, cr, uid, ids, context=None):
        """Calculate the selected balance report data."""
        for id in ids:
            # Send the calculate signal to the balance report to trigger
            # action_calculate.
            wf_service = netsvc.LocalService('workflow')
            wf_service.trg_validate(uid, 'account.balance.reporting', id,
                                    'calculate', cr)
        return 'close'


class AccountBalanceReportingLine(orm.Model):
    """
    Account balance report line / Accounting concept
    One line of detail of the balance report representing an accounting
    concept with its values.
    The accounting concepts follow a parent-children hierarchy.
    Its values (current and previous) are calculated based on the 'value'
    formula of the linked template line.
    """
    _name = "account.balance.reporting.line"

    _columns = {
        'report_id': fields.many2one('account.balance.reporting', 'Report',
                                     ondelete='cascade'),
        'sequence': fields.integer('Sequence', required=True),
        'code': fields.char('Code', size=64, required=True, select=True),
        'name': fields.char('Name', size=256, required=True, select=True),
        'notes': fields.text('Notes'),
        'current_value': fields.float('Fiscal year 1', digits=(16, 2)),
        'previous_value': fields.float('Fiscal year 2', digits=(16, 2)),
        'calc_date': fields.datetime("Calculation date"),
        'css_class': fields.selection(CSS_CLASSES, 'CSS Class'),
        'template_line_id': fields.many2one(
            'account.balance.reporting.template.line',
            'Line template', ondelete='set null'),
        'parent_id': fields.many2one('account.balance.reporting.line',
                                     'Parent', ondelete='cascade'),
        'child_ids': fields.one2many('account.balance.reporting.line',
                                     'parent_id', 'Children'),
    }

    _defaults = {
        'report_id': lambda self, cr, uid, context: context.get('report_id',
                                                                None),
        'css_class': 'default',
        'sequence': 10,
    }

    _order = "sequence, code"

    _sql_constraints = [
        ('report_code_uniq', 'unique(report_id, code)',
         _("The code must be unique for this report!"))
    ]

    def name_get(self, cr, uid, ids, context=None):
        """Redefine the method to show the code in the name ("[code] name")."""
        res = []
        for item in self.browse(cr, uid, ids, context=context):
            res.append((item.id, "[%s] %s" % (item.code, item.name)))
        return res

    def name_search(self, cr, uid, name, args=None, operator='ilike',
                    context=None, limit=80):
        """Redefine the method to allow searching by code."""
        ids = []
        if args is None:
            args = []
        if name:
            ids = self.search(cr, uid, [('code', 'ilike', name)] + args,
                              limit=limit, context=context)
        if not ids:
            ids = self.search(cr, uid, [('name', operator, name)] + args,
                              limit=limit, context=context)
        return self.name_get(cr, uid, ids, context=context)

    def _create_child_lines(self, cr, uid, ids, code, bmode, fyear,
                            context=None):
        acc_obj = self.pool.get('account.account')
        line = self.browse(cr, uid, ids[0], context=context)
        cont = 1000
        for acc_code in re.findall('(-?\w*\(?[0-9a-zA-Z_]*\)?)', code):
            # Check if the code is valid (findall might return empty strings)
            acc_code = acc_code.strip()
            if acc_code:
                sign, acc_code, mode, sign_mode = \
                    self._get_code_sign_mode(acc_code, bmode)

                # Search for the account (perfect match)
                account_ids = acc_obj.search(cr, uid,
                                             [('code', '=', acc_code),
                                              ('company_id', '=',
                                               line.report_id.company_id.id)],
                                             context=context)

                for account in acc_obj.browse(cr, uid, account_ids,
                                              context=context):
                    child_ids = acc_obj.search(cr, uid,
                                               [('id', 'child_of', account.id),
                                                ('level', '<=',
                                                 line.report_id.level)],
                                               order="code asc")
                    for child_account in acc_obj.browse(cr, uid, child_ids,
                                                        context=context):
                        value = 0.0
                        if mode == 'debit':
                            value -= child_account.debit * sign
                        elif mode == 'credit':
                            value += child_account.credit * sign
                        else:
                            value += child_account.balance * sign * sign_mode

                        line_ids = self.search(cr, uid,
                                               [('template_line_id', '=',
                                                line.template_line_id.id),
                                                ('name', '=',
                                                    child_account.code +
                                                    u": " +
                                                    child_account.name),
                                                ('report_id', '=',
                                                 line.report_id.id)])
                        if not line_ids:
                            line_id = self.create(cr, uid, {
                                'code': line.code + u"/" + str(cont),
                                'name': (child_account.code + u": " +
                                         child_account.name),
                                'report_id': line.report_id.id,
                                'template_line_id': line.template_line_id.id,
                                'parent_id': line.id,
                                'current_value': None,
                                'previous_value': None,
                                'sequence': line.sequence,
                                'css_class':
                                (child_account.level and
                                 child_account.level < 5) and
                                u'l' + str(child_account.level)
                                or'default'
                            }, context=context)
                            cont += 1
                        else:
                            line_id = line_ids[0]

                        if line.template_line_id.negate:
                            value = -value
                        vals = {}
                        if fyear == 'current':
                            vals = {'current_value': value,
                                    'calc_date': line.report_id.calc_date}
                        elif fyear == 'previous':
                            vals = {'previous_value': value,
                                    'calc_date': line.report_id.calc_date}
                        self.write(cr, uid, [line_id], vals, context=context)

    def _get_account_balance(self, cr, uid, ids, code, balance_mode=0,
                             context=None):
        """It returns the (debit, credit, balance*) tuple for a account with
        the given code, or the sum of those values for a set of accounts
        when the code is in the form "400,300,(323)"

        Depending on the balance_mode, the balance is calculated as follows:
          Mode 0: debit-credit for all accounts (default);
          Mode 1: debit-credit, credit-debit for accounts in brackets;
          Mode 2: credit-debit for all accounts;
          Mode 3: credit-debit, debit-credit for accounts in brackets.

        Also the user may specify to use only the debit or credit of the
        account instead of the balance writing "debit(551)" or "credit(551)".
        """
        acc_obj = self.pool['account.account']
        logger = logging.getLogger(__name__)
        res = 0.0
        line = self.browse(cr, uid, ids[0], context=context)
        company_id = line.report_id.company_id.id
        # We iterate over the accounts listed in "code", so code can be
        # a string like "430+431+432-438"; accounts split by "+" will be added,
        # accounts split by "-" will be substracted.
        for acc_code in re.findall(r'(-?\w*\(?[0-9a-zA-Z_]*\)?)', code):
            # Check if the code is valid (findall might return empty strings)
            acc_code = acc_code.strip()
            if acc_code:
                sign, acc_code, mode, sign_mode = \
                    self._get_code_sign_mode(acc_code, balance_mode)
                # Search for the account (perfect match)
                account_ids = acc_obj.search(cr, uid, [
                    ('code', '=', acc_code),
                    ('company_id', '=', company_id)
                ], context=context)
                if not account_ids:
                    # Search for a subaccount ending with '0'
                    account_ids = acc_obj.search(cr, uid, [
                        ('code', '=like', '%s%%0' % acc_code),
                        ('company_id', '=', company_id)
                    ], context=context)
                if not account_ids:
                    logger.warning("Account with code '%s' not found!"
                                   % acc_code)
                for account in acc_obj.browse(cr, uid, account_ids,
                                              context=context):
                    if mode == 'debit':
                        res -= account.debit * sign
                    elif mode == 'credit':
                        res += account.credit * sign
                    else:
                        res += account.balance * sign * sign_mode
        return res

    def refresh_values(self, cr, uid, ids, context=None):
        """Recalculates the values of this report line using the
        linked line report values formulas:

        Depending on this formula the final value is calculated as follows:
        - Empy report value: sum of (this concept) children values.
        - Number with decimal point ("10.2"): that value (constant).
        - Account numbers separated by commas ("430,431,(437)"): Sum of the
            account balances.
            (The sign of the balance depends on the balance mode)
        - Concept codes separated by "+" ("11000+12000"): Sum of those
            concepts values.
        """
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            tmpl_line = line.template_line_id
            balance_mode = int(tmpl_line.template_id.balance_mode)
            current_value = 0.0
            previous_value = 0.0
            report = line.report_id
            # We use the same code to calculate both fiscal year values,
            # just iterating over them.
            for fyear in ('current', 'previous'):
                value = 0
                if fyear == 'current':
                    tmpl_value = tmpl_line.current_value
                elif fyear == 'previous':
                    tmpl_value = (tmpl_line.previous_value or
                                  tmpl_line.current_value)
                # Remove characters after a ";" (we use ; for comments)
                if tmpl_value:
                    tmpl_value = tmpl_value.split(';')[0]
                if (fyear == 'current' and not report.current_fiscalyear_id) \
                        or (fyear == 'previous' and
                            not report.previous_fiscalyear_id):
                    value = 0
                else:
                    if not tmpl_value:
                        # Empy template value => sum of the children values
                        for child in line.child_ids:
                            if child.calc_date != child.report_id.calc_date:
                                # Tell the child to refresh its values
                                child.refresh_values()
                                # Reload the child data
                                child = self.browse(cr, uid, child.id,
                                                    context=context)
                            if fyear == 'current':
                                value += child.current_value
                            elif fyear == 'previous':
                                value += child.previous_value
                    elif re.match(r'^\-?[0-9]*\.[0-9]*$', tmpl_value):
                        # Number with decimal points => that number value
                        # (constant).
                        value = float(tmpl_value)
                    elif re.match(r'^[0-9a-zA-Z,\(\)\*_\ ]*$', tmpl_value):
                        # Account numbers separated by commas => sum of the
                        # account balances. We will use the context to filter
                        # the accounts by fiscalyear and periods.
                        ctx = context.copy()
                        if fyear == 'current':
                            ctx.update({
                                'fiscalyear': report.current_fiscalyear_id.id,
                            })
                        elif fyear == 'previous':
                            ctx.update({
                                'fiscalyear': report.previous_fiscalyear_id.id,
                            })
                        if line.report_id.check_filter == 'date':
                            if fyear == 'current':
                                ctx.update({
                                    'date_from': report.current_date_from,
                                    'date_to': report.current_date_to
                                })
                            elif fyear == 'previous':
                                ctx.update({
                                    'date_from': report.previous_date_from,
                                    'date_to': report.previous_date_to
                                })
                        if line.report_id.check_filter == 'period':
                            if fyear == 'current':
                                ctx.update({
                                    'periods':
                                    [p.id for p in report.current_period_ids]
                                })
                            elif fyear == 'previous':
                                ctx.update({
                                    'periods':
                                    [p.id for p in report.previous_period_ids]
                                })
                        value = self._get_account_balance(
                            cr, uid, [line.id], tmpl_value,
                            balance_mode=balance_mode, context=ctx)
                        if line.report_id.level:
                            line._create_child_lines(tmpl_value, balance_mode,
                                                     fyear, context=ctx)
                    elif re.match(r'^[\+\-0-9a-zA-Z_\*\ ]*$', tmpl_value):
                        # Account concept codes separated by "+" => sum of the
                        # concepts (template lines) values.
                        for line_code in re.findall(r'(-?\(?[0-9a-zA-Z_]*\)?)',
                                                    tmpl_value):
                            sign = 1
                            if (line_code.startswith('-') or
                                    (line_code.startswith('(') and
                                     balance_mode in (2, 4))):
                                sign = -1
                            line_code = line_code.strip('-()*')
                            # findall might return empty strings
                            if line_code:
                                # Search for the line (perfect match)
                                line_ids = self.search(cr, uid, [
                                    ('report_id', '=', report.id),
                                    ('code', '=', line_code),
                                ], context=context)
                                for child in self.browse(cr, uid, line_ids,
                                                         context=context):
                                    if (child.calc_date !=
                                            child.report_id.calc_date):
                                        child.refresh_values()
                                        # Reload the child data
                                        child = self.browse(cr, uid, child.id,
                                                            context=context)
                                    if fyear == 'current':
                                        value += child.current_value * sign
                                    elif fyear == 'previous':
                                        value += child.previous_value * sign
                # Negate the value if needed
                if tmpl_line.negate:
                    value = -value
                if fyear == 'current':
                    current_value = value
                elif fyear == 'previous':
                    previous_value = value
            # Write the values
            self.write(cr, uid, line.id, {
                'current_value': current_value,
                'previous_value': previous_value,
                'calc_date': line.report_id.calc_date,
            }, context=context)
        return True

    def _get_code_sign_mode(self, acc_code, balance_mode):
        # Check the sign of the code (substraction)
        if acc_code.startswith('-'):
            sign = -1
            acc_code = acc_code[1:].strip()  # Strip the sign
        else:
            sign = 1
        if re.match(r'^debit\(.*\)$', acc_code):
            # Use debit instead of balance
            mode = 'debit'
            acc_code = acc_code[6:-1]  # Strip debit()
        elif re.match(r'^credit\(.*\)$', acc_code):
            # Use credit instead of balance
            mode = 'credit'
            acc_code = acc_code[7:-1]  # Strip credit()
        else:
            mode = 'balance'
        # Calculate sign of the balance mode
        sign_mode = 1
        if balance_mode in (1, 2, 3):
            # for accounts in brackets or mode 2, the sign is reversed
            if (acc_code.startswith('(') and acc_code.endswith(')')) \
                    or balance_mode == 2:
                sign_mode = -1
        # Strip the brackets (if any)
        if acc_code.startswith('(') and acc_code.endswith(')'):
            acc_code = acc_code[1:-1]

        return sign, acc_code, mode, sign_mode
