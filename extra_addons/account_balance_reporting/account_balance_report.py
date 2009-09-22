# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account balance reporting engine
#    Copyright (C) 2009 Pexego Sistemas Informáticos. All Rights Reserved
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
Account balance report objects

Generic account balance report document (with header and detail lines).
Designed following the needs of the
Spanish/Spain localization.
"""
__author__ = "Borja López Soilán (Pexego)"


from osv import fields, osv
import re
import time


################################################################################
# CSS classes for the account line templates
################################################################################

CSS_CLASSES = [('default','Default'),('l1', 'Level 1'), ('l2', 'Level 2'),
                ('l3', 'Level 3'), ('l4', 'Level 4'), ('l5', 'Level 5')]

################################################################################
# Account balance report (document / header)
################################################################################

class account_balance_report(osv.osv):
    """
    Account balance report.
    It stores the configuration/header fields of an account balance report,
    and the linked lines of detail with the values of the accounting concepts
    (values generated from the selected template lines of detail formulas).
    """

    _name = "account.balance.report"

    _columns = {
        # Name of this report
        'name': fields.char('Name', size=64, required=True, select=True),
        # Template used to calculate this report
        'template_id': fields.many2one('account.balance.report.template', 'Template', ondelete='set null'),
        # Date of the last calculation
        'calc_date': fields.datetime("Calculation date"),
        # State of the report
        'state': fields.selection([('draft','Draft'),('calc','Processing'),('calc_done','Processed'),('done','Done')], 'State'),
        # Company
        'company_id': fields.many2one('res.company', 'Company', readonly=True, ondelete='cascade'),
        #
        # Current fiscal year and it's (selected) periods
        #
        'current_fiscalyear_id': fields.many2one('account.fiscalyear','Fiscal year 1', select=True),
        'current_period_ids': fields.many2many('account.period', 'account_balance_report_account_period_current_rel', 'account_balance_report_id', 'period_id', 'Fiscal year 1 periods'),
        #
        # Previous fiscal year and it's (selected) periods
        #
        'previous_fiscalyear_id': fields.many2one('account.fiscalyear','Fiscal year 2', select=True),
        'previous_period_ids': fields.many2many('account.period', 'account_balance_report_account_period_previous_rel', 'account_balance_report_id', 'period_id', 'Fiscal year 2 periods'),
    }

    _defaults = {
        # Current company by default:
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id,
        # Draft state by default:
        'state': lambda *a: 'draft',
    }

    #
    # Actions ##################################################################
    #

    def action_calculate(self, cr, uid, ids, context=None):
        """
        Called when the user presses the Calculate button.
        It will use the report template to generate lines of detail for the
        report with calculated values.
        """
        report_line_facade = self.pool.get('account.balance.report.line')

        # Set the state to 'calculating'
        self.write(cr, uid, ids, {
                'state': 'calc',
                'calc_date': time.strftime('%Y-%m-%d %H:%M:%S')
            })

        #
        # Replace the lines of detail of the report with new lines from its template
        #

        reports = self.browse(cr, uid, ids, context)
        for report in reports:
            # Clear the report data (unlink the lines of detail)
            report_line_facade.unlink(cr, uid, [line.id for line in report.line_ids])

            #
            # Fill the report with a 'copy' of the lines of its template (if it has one)
            #
            if report.template_id:
                for template_line in report.template_id.line_ids:
                    report_line_facade.create(cr, uid, {
                            'code': template_line.code,
                            'name': template_line.name,
                            'report_id': report.id,
                            'template_line_id': template_line.id,
                            'parent_id': None,
                            'current_value': None,
                            'previous_value': None,
                            'sequence': template_line.sequence,
                            'css_class': template_line.css_class,
                        }, context)

        #
        # Set the parents of the lines in the report
        # Note: We reload the reports objects to refresh the lines of detail.
        #
        reports = self.browse(cr, uid, ids, context)
        for report in reports:
            if report.template_id:
                #
                # Establecemos los padres de las líneas (ahora que ya están creados)
                #
                for line in report.line_ids:
                    if line.template_line_id and line.template_line_id.parent_id:
                        parent_line_id = report_line_facade.search(cr, uid, [('report_id', '=', report.id), ('code', '=', line.template_line_id.parent_id.code)])
                        report_line_facade.write(cr, uid, line.id, {
                                'parent_id': len(parent_line_id) and parent_line_id[0] or None,
                            }, context)
                        
        #
        # Calculate the values of the lines
        # Note: We reload the reports objects to refresh the lines of detail.
        #
        reports = self.browse(cr, uid, ids, context)
        for report in reports:
            if report.template_id:
                # Refresh the report's lines values
                for line in report.line_ids:
                    line.refresh_values()

                # Set the report as calculated
                self.write(cr, uid, [report.id], {
                        'state': 'calc_done'
                    })
            else:
                # Ouch! no template: Going back to draft state.
                self.write(cr, uid, [report.id], {'state': 'draft'})
        return True

    def action_calculated(self, cr, uid, ids, context=None):
        """
        Called when the calculation ends.
        """
        # TODO: Send a notice to the user about the report calculation results?
        return True

    def action_confirm(self, cr, uid, ids, context=None):
        """
        Called when the user clicks the confirm button.
        """
        self.write(cr, uid, ids, {'state': 'done'})
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        """
        Called when the user clicks the cancel button.
        """
        self.write(cr, uid, ids, {'state': 'draft', 'calc_date': None})
        return True

account_balance_report()



################################################################################
# Account balance report line of detail (accounting concept)
################################################################################

class account_balance_report_line(osv.osv):
    """
    Account balance report line / Accounting concept
    One line of detail of the balance report representing an accounting
    concept with its values.
    The accounting concepts follow a parent-children hierarchy. 
    Its values (current and previous) are calculated based on the 'value'
    formula of the linked template line.
    """

    _name = "account.balance.report.line"

    _columns = {
        # Parent report of this line
        'report_id': fields.many2one('account.balance.report', 'Report', ondelete='cascade'),

        # Concept official code (as specified by normalized models, will be used when printing)
        'code': fields.char('Code', size=64, required=True, select=True),
        # Concept official name (will be used when printing)
        'name': fields.char('Name', size=256, required=True, select=True),
        # Notes value (references to the notes)
        'notes': fields.text('Notes'),
        # Concept value in this fiscal year
        'current_value': fields.float('Fiscal year 1', digits=(16,2)),
        # Concept value on the previous fiscal year
        'previous_value': fields.float('Fiscal year 2', digits=(16,2)),
        # Date of the last calculation
        'calc_date': fields.datetime("Calculation date"),

        # Order sequence, it's also used for grouping into sections, that's why it is a char
        'sequence': fields.char('Sequence', size=32, required=False),
        # CSS class, used when printing to set the style of the line
        'css_class': fields.selection(CSS_CLASSES, 'CSS Class', required=False),

        # Linked template line used to calculate this line values
        'template_line_id': fields.many2one('account.balance.report.template.line', 'Line template', ondelete='set null'),
        # Parent accounting concept
        'parent_id': fields.many2one('account.balance.report.line', 'Parent', ondelete='cascade'),
        # Children accounting concepts
        'child_ids': fields.one2many('account.balance.report.line', 'parent_id', 'Children'),
    }

    _defaults = {
        # Use context report_id as the the parent report
        'report_id': lambda self, cr, uid, context: context.get('report_id', None),
        # Default css class (so we always have a class)
        'css_class': 'default',
    }

    # Lines are sorted by its sequence and code
    _order = "sequence, code"

    # Don't let the user repeat codes in the report (the codes will be used to look up accounting concepts)
    _sql_constraints = [
        ('report_code_uniq', 'unique (report_id,code)', _("The code must be unique for this report!"))
    ]



    def name_get(self, cr, uid, ids, context=None):
        """
        Redefine the name_get method to show the code in the name ("[code] name").
        """
        if not len(ids):
            return []
        res=[]
        for item in self.browse(cr,uid,ids):
            res.append((item.id, "[%s] %s" % (item.code, item.name)))
        return res


    def name_search(self, cr, uid, name, args=[], operator='ilike', context={}, limit=80):
        """
        Redefine the name_search method to allow searching by code.
        """
        ids = []
        if name:
            ids = self.search(cr, uid, [('code','ilike',name)]+ args, limit=limit)
        if not ids:
            ids = self.search(cr, uid, [('name',operator,name)]+ args, limit=limit)
        return self.name_get(cr, uid, ids, context=context)


    def refresh_values(self, cr, uid, ids, context=None):
        """
        Recalculates the values of this report line using the
        linked line template values formulas:

        - Empy template value => sum of the children, of this concept, values.
        - Number with decimal points ("10.2") => that number value (constant).
        - Account numbers separated by commas ("430,431,(437)") => sum of the account balances.
        - Account concept codes separated by "+" ("11000+12000") => sum of the concept (report lines) values.
        """
        for line in self.browse(cr, uid, ids):
            current_value = 0.0
            previous_value = 0.0

            #
            # We use the same code to calculate both fiscal year values,
            # just iterating over them.
            #
            for fyear in ('current', 'previous'):
                value = 0
                if fyear == 'current':
                    template_value = line.template_line_id.current_value
                elif fyear == 'previous':
                    template_value = line.template_line_id.previous_value

                # Remove characters after a ";" (we use ; for comments)
                template_value = template_value.split(';')[0]

                #
                # Calculate the value
                #
                if not template_value:
                    #
                    # Empy template value => sum of the children, of this concept, values.
                    #
                    for child in line.child_ids:
                        if child.calc_date != child.report_id.calc_date:
                            # Tell the child to refresh its values
                            child.refresh_values()
                            # Reload the child data
                            child = self.browse(cr, uid, [child.id])[0]
                        if fyear == 'current':
                            value += float(child.current_value)
                        elif fyear == 'previous':
                            value += float(child.previous_value)

                elif re.match(r'^\-?[0-9]*\.[0-9]*$', template_value):
                    #
                    # Number with decimal points => that number value (constant).
                    #
                    value = float(template_value)

                elif re.match(r'^[0-9a-zA-Z,\(\)\*_]*$', template_value):
                    #
                    # Account numbers separated by commas => sum of the account balances.
                    #
                    # We will use the context to filter the accounts by fiscalyear
                    # and periods.
                    #
                    if fyear == 'current':
                        ctx = {
                            'fiscalyear': line.report_id.current_fiscalyear_id.id,
                            'periods': [p.id for p in line.report_id.current_period_ids],
                        }
                    elif fyear == 'previous':
                        ctx = {
                            'fiscalyear': line.report_id.previous_fiscalyear_id.id,
                            'periods': [p.id for p in line.report_id.previous_period_ids],
                        }
                    dcb = line._get_account_debit_credit_and_balance(template_value, ctx)
                    value = dcb[2]

                elif re.match(r'^[\+\-0-9a-zA-Z_\*]*$', template_value):
                    #
                    # Account concept codes separated by "+" => sum of the concept (report lines) values.
                    #
                    for line_code in re.findall(r'(-?\(?[0-9a-zA-Z_]*\)?)', template_value):
                        # Check the sign of the code (substraction)
                        if line_code.startswith('-') or line_code.startswith('('):
                            sign = -1.0
                        else:
                            sign = 1.0
                        line_code = line_code.strip('-()*')
                        
                        # Check if the code is valid (findall might return empty strings)
                        if len(line_code) > 0:
                            # Search for the line (perfect match)
                            line_ids = self.search(cr, uid, [
                                    ('report_id','=', line.report_id.id),
                                    ('code', '=', line_code),
                                ])  
                            for child in self.browse(cr, uid, line_ids):
                                if child.calc_date != child.report_id.calc_date:
                                    # Tell the child to refresh its values
                                    child.refresh_values()
                                    # Reload the child data
                                    child = self.browse(cr, uid, [child.id])[0]
                                if fyear == 'current':
                                    value += float(child.current_value) * sign
                                elif fyear == 'previous':
                                    value += float(child.previous_value) * sign
                if fyear == 'current':
                    current_value = value
                elif fyear == 'previous':
                    previous_value = value
                    
            # Write the values
            self.write(cr, uid, [line.id], {
                    'current_value': current_value,
                    'previous_value': previous_value,
                    'calc_date': line.report_id.calc_date
                })
        return True


    def _get_account_debit_credit_and_balance(self, cr, uid, ids, code, context=None):
        """
        It returns the (debit, credit, balance) tuple for a account with the
        given code, or the sum of those values for a set of accounts
        when the code is in the form "400,300,(323)"
        """
        acc_facade = self.pool.get('account.account')
        res = [0.0, 0.0, 0.0]
        line = self.browse(cr, uid, ids)[0]
        
        # We iterate over the accounts listed in "code", so code can be
        # a string like "430+431+432-438"; accounts split by "+" will be added,
        # accounts split by "-" will be substracted.
        for account_code in re.findall('(-?\(?[0-9a-zA-Z_]*\)?)', code):
            # Check the sign of the code (substraction)
            if account_code.startswith('-') or account_code.startswith('('):
                sign = -1.0
            else:
                sign = 1.0
            account_code = account_code.strip('-()')

            # Check if the code is valid (findall might return empty strings)
            if len(account_code) > 0:
                # Search for the account (perfect match)
                account_ids = acc_facade.search(cr, uid, [
                        ('code', '=', account_code),
                        ('company_id','=', line.report_id.company_id.id)
                    ], context=context)
                if len(account_ids) == 0:
                    # We didn't find the account, search for a subaccount ending with '0'
                    account_ids = acc_facade.search(cr, uid, [
                            ('code', '=like', '%s%%0' % account_code),
                            ('company_id','=', line.report_id.company_id.id)
                        ], context=context)
                if len(account_ids) > 0:
                    res[0] += acc_facade.browse(cr, uid, account_ids, context)[0].debit * sign
                    res[1] += acc_facade.browse(cr, uid, account_ids, context)[0].credit * sign
                    res[2] += acc_facade.browse(cr, uid, account_ids, context)[0].balance * sign
        return res


account_balance_report_line()


class account_balance_report_withlines(osv.osv):
    """
    Extend the 'account balance report' to add a link to its
    lines of detail.
    """

    _inherit = "account.balance.report"

    _columns = {
        'line_ids': fields.one2many('account.balance.report.line', 'report_id', 'Lines'),
    }

account_balance_report_withlines()




