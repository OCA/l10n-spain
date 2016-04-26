# -*- coding: utf-8 -*-
# © 2009 Pexego/Comunitea
# © 2016 Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0).

from openerp import api, fields, models, _
from .account_balance_reporting_template import CSS_CLASSES
import re
import logging


class AccountBalanceReporting(models.Model):
    _name = "account.balance.reporting"
    _description = (
        "It stores the configuration/header fields of an account balance "
        "report, and the linked lines of detail with the values of the "
        "accounting concepts (values generated from the selected template "
        "lines of detail formulas)")

    READONLY_STATES = {'calc_done': [('readonly', True)],
                       'done': [('readonly', True)]}

    @api.model
    def _get_levels(self):
        # This can't be filtered by company because we can change the company
        # on the fly
        self.env.cr.execute(
            "SELECT DISTINCT(level) FROM account_account ORDER BY level")
        reg = self.env.cr.fetchall()
        return [(str(x[0]), str(x[0])) for x in reg if x[0]]

    name = fields.Char(string='Name', required=True, index=True)
    template_id = fields.Many2one(
        comodel_name='account.balance.reporting.template',
        string='Template', ondelete='set null', required=True, index=True,
        states=READONLY_STATES)
    calc_date = fields.Datetime(string="Calculation date", readonly=True)
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('calc_done', 'Processed'),
                   ('done', 'Done'),
                   ('canceled', 'Canceled')],
        string='State', default='draft')
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', ondelete='cascade',
        required=True, readonly=False, states=READONLY_STATES,
        default=lambda self: self.env.user.company_id.id)
    check_filter = fields.Selection(
        selection=[('periods', 'Periods'),
                   ('dates', 'Dates')],
        default='periods', string='Compute by', required=True,
        states=READONLY_STATES)
    level = fields.Selection(
        selection=_get_levels, string='Level', states=READONLY_STATES)
    current_fiscalyear_id = fields.Many2one(
        comodel_name='account.fiscalyear', string='Fiscal year 1', index=True,
        required=True, states=READONLY_STATES)
    current_period_ids = fields.Many2many(
        comodel_name='account.period',
        relation='account_balance_reporting_account_period_current_rel',
        column1='account_balance_reporting_id', column2='period_id',
        string='Fiscal year 1 periods', states=READONLY_STATES)
    current_date_from = fields.Date(
        string='Date From', states=READONLY_STATES)
    current_date_to = fields.Date(
        string='Date To', states=READONLY_STATES)
    previous_fiscalyear_id = fields.Many2one(
        comodel_name='account.fiscalyear', string='Fiscal year 2', index=True,
        states=READONLY_STATES)
    previous_period_ids = fields.Many2many(
        comodel_name='account.period',
        relation='account_balance_reporting_account_period_previous_rel',
        column1='account_balance_reporting_id', column2='period_id',
        string='Fiscal year 2 periods', states=READONLY_STATES)
    previous_date_from = fields.Date(
        string='Date From', states=READONLY_STATES)
    previous_date_to = fields.Date(
        string='Date To', states=READONLY_STATES)
    line_ids = fields.One2many(
        comodel_name='account.balance.reporting.line',
        inverse_name='report_id', string='Lines',
        states={'done': [('readonly', True)]})

    @api.multi
    def action_calculate(self):
        """Called when the user presses the Calculate button.
        It will use the report template to generate lines of detail for the
        report with calculated values."""
        line_obj = self.env['account.balance.reporting.line']
        for report in self:
            # Clear the report data (unlink the lines of detail)
            report.line_ids.unlink()
            # Fill the report with a 'copy' of the lines of its template
            # (if it has one)
            for template_line in report.template_id.line_ids:
                line_obj.create({
                    'code': template_line.code,
                    'name': template_line.name,
                    'report_id': report.id,
                    'template_line_id': template_line.id,
                    'parent_id': None,
                    'current_value': None,
                    'previous_value': None,
                    'sequence': template_line.sequence,
                    'css_class': template_line.css_class,
                })
            # Set line parents (now that they have been created)
            for line in report.line_ids:
                tmpl_line = line.template_line_id
                if line.template_line_id.parent_id:
                    parent_line_ids = line_obj.search(
                        [('report_id', '=', report.id),
                         ('code', '=', tmpl_line.parent_id.code)])
                    line.parent_id = parent_line_ids[:1].id
            # Refresh the report's lines values
            report.write({
                'state': 'calc_done',
                'calc_date': fields.Datetime.now()
            })
            report.line_ids.refresh_values()
        return True

    @api.multi
    def action_confirm(self):
        """Called when the user clicks the confirm button."""
        self.write({'state': 'done'})
        return True

    @api.multi
    def action_cancel(self):
        """Called when the user clicks the cancel button."""
        self.write({'state': 'canceled'})
        return True

    @api.multi
    def action_recover(self):
        """Called when the user clicks the draft button to create
        a new workflow instance."""
        self.write({'state': 'draft', 'calc_date': None})
        return True


class AccountBalanceReportingLine(models.Model):
    _name = "account.balance.reporting.line"
    _order = "sequence, code"
    _description = (
        "Account balance report line / Accounting concept. One line of detail "
        "of the balance report representing an accounting concept with its "
        "values. The accounting concepts follow a parent-children hierarchy. "
        "Its values (current and previous) are calculated based on the "
        "'value' formula of the linked template line.")

    report_id = fields.Many2one(
        comodel_name='account.balance.reporting', string='Report',
        ondelete='cascade')
    sequence = fields.Integer(string='Sequence', required=True, default=10)
    code = fields.Char(string='Code', required=True, index=True)
    name = fields.Char(string='Name', required=True, index=True)
    display_name = fields.Char(
        string='Name', compute='_compute_display_name', store=True, index=True)
    notes = fields.Text('Notes')
    current_value = fields.Float(string='Fiscal year 1', digits=(16, 2))
    previous_value = fields.Float(string='Fiscal year 2', digits=(16, 2))
    calc_date = fields.Datetime(string="Calculation date")
    css_class = fields.Selection(
        selection=CSS_CLASSES, string='CSS Class', default='default')
    template_line_id = fields.Many2one(
        comodel_name='account.balance.reporting.template.line',
        string='Line template', ondelete='set null')
    parent_id = fields.Many2one(
        comodel_name='account.balance.reporting.line',
        string='Parent', ondelete='cascade')
    child_ids = fields.One2many(
        comodel_name='account.balance.reporting.line',
        inverse_name='parent_id', string='Children')
    current_move_line_ids = fields.Many2many(
        comodel_name="account.move.line", string="Journal items (current)")
    current_move_line_count = fields.Integer(
        compute="_current_move_line_count")
    previous_move_line_ids = fields.Many2many(
        comodel_name="account.move.line", string="Journal items (previous)")
    previous_move_line_count = fields.Integer(
        compute="_previous_move_line_count")

    _sql_constraints = [
        ('report_code_uniq', 'unique(report_id, code)',
         _("The code must be unique for this report!"))
    ]

    @api.multi
    @api.depends('name', 'css_class')
    def _compute_display_name(self):
        for line in self:
            level = (
                line.css_class[1:].isdigit() and int(line.css_class[1:]) or 1)
            line.display_name = '..' * (level - 1) + line.name

    @api.multi
    def _current_move_line_count(self):
        for line in self:
            line.current_move_line_count = len(line.current_move_line_ids)

    @api.multi
    def _previous_move_line_count(self):
        for line in self:
            line.previous_move_line_count = len(line.previous_move_line_ids)

    @api.multi
    def name_get(self):
        """Redefine the method to show the code in the name ("[code] name")."""
        res = []
        for item in self:
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

    @api.multi
    def _create_child_lines(self, domain, expr, balance_mode, fyear):
        self.ensure_one()
        move_line_obj = self.env['account.move.line']
        account_obj = self.env['account.account']
        cont = 1000
        for code in re.findall(r'(-?\w*\(?[0-9a-zA-Z_]*\)?)', expr):
            # Check if the code is valid (findall might return empty
            # strings)
            code = code.strip()
            if not code:
                continue
            sign, acc_code, mode, sign_mode = self._get_code_sign_mode(
                code, balance_mode)
            # Search for the account (perfect match)
            accounts = account_obj.search(
                [('code', '=', acc_code),
                 ('company_id', '=', self.report_id.company_id.id)])
            for account in accounts:
                child_accounts = account_obj.search(
                    [('id', 'child_of', account.id),
                     ('level', '<=', self.report_id.level)],
                    order="code asc")
                for child_account in child_accounts:
                    value = 0.0
                    domain_account = list(domain)
                    domain_account.append(
                        ('account_id', 'in', child_account.ids))
                    group = move_line_obj.read_group(
                        domain_account, ['debit', 'credit'], [])[0]
                    if mode == 'debit':
                        value -= (group['debit'] or 0.0) * sign
                    elif mode == 'credit':
                        value += (group['credit'] or 0.0) * sign
                    else:
                        value += (
                            sign * sign_mode * ((group['debit'] or 0.0) -
                                                (group['credit'] or 0.0)))
                    report_line = self.search(
                        [('template_line_id', '=', self.template_line_id.id),
                         ('name', '=', child_account.code + u": " +
                          child_account.name),
                         ('report_id', '=', self.report_id.id)], limit=1)
                    if not report_line:
                        report_line = self.create({
                            'code': self.code + u"/" + str(cont),
                            'name': (child_account.code + u": " +
                                     child_account.name),
                            'report_id': self.report_id.id,
                            'template_line_id': self.template_line_id.id,
                            'parent_id': self.id,
                            'current_value': None,
                            'previous_value': None,
                            'sequence': self.sequence,
                            'css_class':
                            (child_account.level and
                             child_account.level < 5) and
                            u'l' + str(child_account.level) or'default'
                        })
                        cont += 1
                    if self.template_line_id.negate:
                        value = -value
                    vals = {}
                    if fyear == 'current':
                        vals = {'current_value': value,
                                'calc_date': self.report_id.calc_date}
                    elif fyear == 'previous':
                        vals = {'previous_value': value,
                                'calc_date': self.report_id.calc_date}
                    report_line.write(vals)
                    report_line.refresh()

    @api.multi
    def _get_account_balance(self, expr, domain, balance_mode=0):
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
        move_line_obj = self.env['account.move.line']
        account_obj = self.env['account.account']
        logger = logging.getLogger(__name__)
        res = 0.0
        company_id = self[:1].report_id.company_id.id
        # We iterate over the accounts listed in "code", so code can be
        # a string like "430+431+432-438"; accounts split by "+" will be added,
        # accounts split by "-" will be substracted.
        move_lines = self.env['account.move.line']
        for code in re.findall(r'(-?\w*\(?[0-9a-zA-Z_]*\)?)', expr):
            # Check if the code is valid (findall might return empty strings)
            code = code.strip()
            if not code:
                continue
            sign, acc_code, mode, sign_mode = self._get_code_sign_mode(
                code, balance_mode)
            # Search for the account (perfect match)
            accounts = account_obj.search(
                [('code', '=', acc_code), ('company_id', '=', company_id)])
            if not accounts:
                # Search for a subaccount ending with '0'
                accounts = account_obj.search(
                    [('code', '=like', '%s%%0' % acc_code),
                     ('company_id', '=', company_id)])
            if not accounts:
                logger.warning("Account with code '%s' not found!", acc_code)
                continue
            account_ids = accounts._get_children_and_consol()
            domain_account = list(domain)
            domain_account.append(('account_id', 'in', account_ids))
            group = move_line_obj.read_group(
                domain_account, ['debit', 'credit'], [])[0]
            move_lines += move_line_obj.search(domain_account)
            if mode == 'debit':
                res -= (group['debit'] or 0.0) * sign
            elif mode == 'credit':
                res += (group['credit'] or 0.0) * sign
            else:
                res += (sign * sign_mode *
                        ((group['debit'] or 0.0) - (group['credit'] or 0.0)))
        return res, move_lines

    @api.multi
    def _calculate_value(self, domain, fyear='current'):
        self.ensure_one()
        tmpl_line = self.template_line_id
        balance_mode = int(tmpl_line.template_id.balance_mode)
        report = self.report_id
        move_lines = self.env['account.move.line']
        value = 0
        if fyear == 'current':
            tmpl_value = tmpl_line.current_value
        else:
            tmpl_value = (tmpl_line.previous_value or
                          tmpl_line.current_value)
        # Remove characters after a ";" (we use ; for comments)
        tmpl_value = (tmpl_value or '').split(';')[0]
        if (fyear == 'current' and not report.current_fiscalyear_id) \
                or (fyear == 'previous' and
                    not report.previous_fiscalyear_id):
            return value, move_lines
        if not tmpl_value:
            # Empy template value => sum of the children values
            for child_line in self.child_ids:
                # Tell the child to refresh its values
                child_line.refresh_values()
                value += (child_line.current_value if fyear == 'current' else
                          child_line.previous_value)
                move_lines += (
                    child_line.current_move_line_ids if fyear == 'current' else
                    child_line.previous_move_line_ids)
        elif re.match(r'^\-?[0-9]*\.[0-9]*$', tmpl_value):
            # Number with decimal points => that number value
            # (constant).
            value = float(tmpl_value)
        elif re.match(r'^[0-9a-zA-Z,\(\)\*_\ ]*$', tmpl_value):
            # Account numbers separated by commas => sum of the
            # account balances. We will use the context to filter
            # the accounts by fiscalyear and periods.
            value, move_lines = self._get_account_balance(
                tmpl_value, domain, balance_mode=balance_mode)
            if self.report_id.level:
                self._create_child_lines(
                    domain, tmpl_value, balance_mode, fyear)
        elif re.match(r'^[\+\-0-9a-zA-Z_\*\ ]*$', tmpl_value):
            # Account concept codes separated by "+" => sum of the
            # concepts (template lines) values.
            for line_code in re.findall(
                    r'(-?\(?[0-9a-zA-Z_]*\)?)', tmpl_value):
                sign = 1
                if (line_code.startswith('-') or
                        (line_code.startswith('(') and
                         balance_mode in (2, 4))):
                    sign = -1
                line_code = line_code.strip('-()*')
                # findall might return empty strings
                if not line_code:
                    continue
                # Search for the line (perfect match)
                code_lines = self.report_id.line_ids.filtered(
                    lambda l: l.code == line_code)
                for code_line in code_lines:
                    code_line.refresh_values()
                    value += (code_line.current_value * sign if
                              fyear == 'current' else
                              code_line.previous_value * sign)
                    move_lines += (
                        code_line.current_move_line_ids if
                        fyear == 'current' else
                        code_line.previous_move_line_ids)
        value = -value if tmpl_line.negate else value
        return value, move_lines

    @api.multi
    def refresh_values(self):
        """Recalculates the values of report lines using the
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
        for report in self.mapped('report_id'):
            domain_current = []
            # Compute current fiscal year
            if report.check_filter == 'dates':
                domain_current += [('date', '>=', report.current_date_from),
                                   ('date', '<=', report.current_date_to)]
            elif report.check_filter == 'periods':
                if report.current_period_ids:
                    periods = report.current_period_ids
                else:
                    periods = report.current_fiscalyear_id.period_ids
                domain_current += [('period_id', 'in', periods.ids)]
            # Compute previous fiscal year
            domain_previous = []
            if report.check_filter == 'dates':
                domain_previous += [('date', '>=', report.previous_date_from),
                                    ('date', '<=', report.previous_date_to)]
            elif report.check_filter == 'periods':
                if report.previous_period_ids:
                    periods = report.previous_period_ids
                else:
                    periods = report.previous_fiscalyear_id.period_ids
                domain_previous += [('period_id', 'in', periods.ids)]
            for line in self.filtered(lambda l: l.report_id == report):
                if (line.calc_date and
                        line.calc_date == line.report_id.calc_date):
                    continue
                current_amount, current_move_lines = line._calculate_value(
                    domain_current, 'current')
                previous_amount, previous_move_lines = line._calculate_value(
                    domain_previous, 'previous')
                line.write({
                    'current_value': current_amount,
                    'previous_value': previous_amount,
                    'calc_date': line.report_id.calc_date,
                    'current_move_line_ids': [(6, 0, current_move_lines.ids)],
                    'previous_move_line_ids': [
                        (6, 0, previous_move_lines.ids)],
                })
                line.refresh()
        return True

    @api.model
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

    @api.model
    def _get_move_line_action_window(self):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'name': _('Journal Items'),
            'res_model': 'account.move.line',
            'target': 'current',
        }

    @api.multi
    def show_move_lines_current(self):
        self.ensure_one()
        res = self._get_move_line_action_window()
        res['domain'] = [('id', 'in', self.current_move_line_ids.ids)]
        return res

    @api.multi
    def show_move_lines_previous(self):
        self.ensure_one()
        res = self._get_move_line_action_window()
        res['domain'] = [('id', 'in', self.previous_move_line_ids.ids)]
        return res
