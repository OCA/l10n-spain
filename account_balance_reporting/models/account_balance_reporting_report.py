# -*- coding: utf-8 -*-
# © 2009 Pexego/Comunitea
# © 2016 Pedro M. Baeza
# © 2016 Vicent Cubells
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

    name = fields.Char(string='Name', required=True, index=True)
    template_id = fields.Many2one(
        comodel_name='account.balance.reporting.template',
        string='Template', ondelete='set null', required=True, index=True,
        states=READONLY_STATES)
    current_date_range = fields.Many2one(
        comodel_name='date.range', string='Date range', states=READONLY_STATES,
    )
    previous_date_range = fields.Many2one(
        comodel_name='date.range', string='Date range', states=READONLY_STATES,
    )
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
        default=lambda self: self.env.user.company_id)
    current_date_from = fields.Date(
        string='Date From',
        states=READONLY_STATES,
        required=True,
    )
    current_date_to = fields.Date(
        string='Date To',
        states=READONLY_STATES,
        required=True,
    )
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

    @api.multi
    @api.onchange('current_date_range')
    def onchange_current_date_range(self):
        if self.current_date_range:
            self.current_date_from = self.current_date_range.date_start
            self.current_date_to = self.current_date_range.date_end

    @api.multi
    @api.onchange('previous_date_range')
    def onchange_previous_date_range(self):
        if self.previous_date_range:
            self.previous_date_from = self.previous_date_range.date_start
            self.previous_date_to = self.previous_date_range.date_end


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
        compute="_compute_current_move_line_count")
    previous_move_line_ids = fields.Many2many(
        comodel_name="account.move.line", string="Journal items (previous)",
        relation="account_balance_reporting_line_previous_move_line_rel",
        column1="line_id", column2="report_id")
    previous_move_line_count = fields.Integer(
        compute="_compute_previous_move_line_count")

    _sql_constraints = [
        ('report_code_uniq', 'unique(report_id, code)',
         _("The code must be unique for this report!"))
    ]

    @api.multi
    @api.depends('name', 'css_class')
    def _compute_display_name(self):
        for line in self:
            level = (
                line.css_class[1:].isdigit() and int(line.css_class[1:]) or 1
            )
            line.display_name = '..' * (level - 1) + (line.name or '')

    @api.multi
    @api.depends('current_move_line_ids')
    def _compute_current_move_line_count(self):
        for line in self:
            line.current_move_line_count = len(line.current_move_line_ids)

    @api.multi
    @api.depends('previous_move_line_ids')
    def _compute_previous_move_line_count(self):
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
        for code in re.findall(r'(-?\w*\(?[0-9a-zA-Z\*_]*\)?)', expr):
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
                if acc_code[-1:] == '*':
                    acc_code = acc_code[:-1]
                # Search for accounts with this prefix
                accounts = account_obj.search(
                    [('code', '=like', '%s%%' % acc_code),
                     ('company_id', '=', company_id)])
            if not accounts:  # pragma: no cover
                logger.warning("Account with code '%s' not found!", acc_code)
                continue
            domain_account = list(domain)
            domain_account.append(
                ('account_id', 'in', [x.id for x in accounts]))
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
        move_lines = self.env['account.move.line']
        value = 0
        if fyear == 'current':
            tmpl_value = tmpl_line.current_value
        else:
            tmpl_value = (tmpl_line.previous_value or
                          tmpl_line.current_value)
        # Remove characters after a ";" (we use ; for comments)
        tmpl_value = (tmpl_value or '').split(';')[0]
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
        - Empty report value: sum of (this concept) children values.
        - Number with decimal point ("10.2"): that value (constant).
        - Account numbers separated by commas ("430,431,(437)"): Sum of the
            account balances.
            (The sign of the balance depends on the balance mode)
        - Concept codes separated by "+" ("11000+12000"): Sum of those
            concepts values.
        """
        for report in self.mapped('report_id'):
            domain_current = []
            # Compute current date range
            domain_current += [('date', '>=', report.current_date_from),
                               ('date', '<=', report.current_date_to)]
            # Compute previous date range
            domain_previous = []
            domain_previous += [('date', '>=', report.previous_date_from),
                                ('date', '<=', report.previous_date_to)]
            # Exclude closing/opening/PL moves (if account_fiscal_year_closing
            # is installed)
            if 'closing_type' in self.env['account.move']._fields:
                domain_current.append(('move_id.closing_type', '=', 'none'))
                domain_previous.append(('move_id.closing_type', '=', 'none'))
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
                # HACK: For assuring the values got updated on call loop
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
