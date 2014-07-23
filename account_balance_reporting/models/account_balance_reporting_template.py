# -*- coding: utf-8 -*-
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
Account balance report templates

Generic account balance report template that will be used to define
accounting concepts with formulas to calculate its values/balance.
Designed following the needs of the Spanish/Spain localization.
"""

from openerp.osv import orm, fields
from openerp.tools.translate import _

_BALANCE_MODE_HELP = (
    """Formula calculation mode: Depending on it, the balance is calculated as
    follows:
      Mode 0: debit-credit (default);
      Mode 1: debit-credit, credit-debit for accounts in brackets;
      Mode 2: credit-debit;
      Mode 3: credit-debit, debit-credit for accounts in brackets.""")

_VALUE_FORMULA_HELP = (
    """Value calculation formula: Depending on this formula the final value is
    calculated as follows:
      Empy template value: sum of (this concept) children values.
      Number with decimal point ("10.2"): that value (constant).
      Account numbers separated by commas ("430,431,(437)"): Sum of the account
          balances (the sign of the balance depends on the balance mode).
      Concept codes separated by "+" ("11000+12000"): Sum of those concepts
      values.
    """)

# CSS classes for the account lines
CSS_CLASSES = [('default', 'Default'),
               ('l1', 'Level 1'),
               ('l2', 'Level 2'),
               ('l3', 'Level 3'),
               ('l4', 'Level 4'),
               ('l5', 'Level 5')]


class AccountBalanceReportingTemplate(orm.Model):
    """
    Account balance report template.
    It stores the header fields of an account balance report template,
    and the linked lines of detail with the formulas to calculate
    the accounting concepts of the report.
    """
    _name = "account.balance.reporting.template"

    _columns = {
        'name': fields.char('Name', size=64, required=True, select=True),
        'type': fields.selection([('system', 'System'),
                                  ('user', 'User')], 'Type'),
        'report_xml_id': fields.many2one('ir.actions.report.xml',
                                         'Report design', ondelete='set null'),
        'description': fields.text('Description'),
        'balance_mode': fields.selection(
            [('0', 'Debit-Credit'),
             ('1', 'Debit-Credit, reversed with brackets'),
             ('2', 'Credit-Debit'),
             ('3', 'Credit-Debit, reversed with brackets')],
            'Balance mode', help=_BALANCE_MODE_HELP),
        'line_ids': fields.one2many('account.balance.reporting.template.line',
                                    'template_id', 'Lines'),
    }

    _defaults = {
        'type': 'user',
        'balance_mode': '0',
    }

    def copy(self, cr, uid, id, default=None, context=None):
        """
        Redefine the copy method to perform it correctly as the line
        structure is a graph.
        """
        if context is None:
            context = {}
        line_obj = self.pool['account.balance.reporting.template.line']
        # Read the current item data:
        template = self.browse(cr, uid, id, context=context)
        # Create the template
        new_id = self.create(cr, uid, {
            'name': '%s*' % template.name,
            'type': 'user',  # Copies are always user templates
            'report_xml_id': template.report_xml_id.id,
            'description': template.description,
            'balance_mode': template.balance_mode,
            'line_ids': None,
        }, context=context)
        # Now create the lines (without parents)
        for line in template.line_ids:
            line_obj.create(cr, uid, {
                'template_id': new_id,
                'sequence': line.sequence,
                'css_class': line.css_class,
                'code': line.code,
                'name': line.name,
                'current_value': line.current_value,
                'previous_value': line.previous_value,
                'negate': line.negate,
                'parent_id': None,
                'child_ids': None,
            }, context=context)
        # Now set the (lines) parents
        for line in template.line_ids:
            if line.parent_id:
                # Search for the copied line
                new_line_id = line_obj.search(cr, uid, [
                    ('template_id', '=', new_id),
                    ('code', '=', line.code),
                ], context=context)[0]
                # Search for the copied parent line
                new_parent_id = line_obj.search(cr, uid, [
                    ('template_id', '=', new_id),
                    ('code', '=', line.parent_id.code),
                ], context=context)[0]
                # Set the parent
                line_obj.write(cr, uid, new_line_id, {
                    'parent_id': new_parent_id,
                }, context=context)
        return new_id


class AccountBalanceReportingTemplateLine(orm.Model):
    """
    Account balance report template line / Accounting concept template
    One line of detail of the balance report representing an accounting
    concept with the formulas to calculate its values.
    The accounting concepts follow a parent-children hierarchy.
    """
    _name = "account.balance.reporting.template.line"

    _columns = {
        'template_id': fields.many2one('account.balance.reporting.template',
                                       'Template', ondelete='cascade'),
        'sequence': fields.integer(
            'Sequence', required=True,
            help="Lines will be sorted/grouped by this field"),
        'css_class': fields.selection(CSS_CLASSES, 'CSS Class', required=False,
                                      help="Style-sheet class"),
        'code': fields.char('Code', size=64, required=True, select=True,
                            help="Concept code, may be used on formulas to "
                                 "reference this line"),
        'name': fields.char('Name', size=256, required=True, select=True,
                            help="Concept name/description"),
        'current_value': fields.text('Fiscal year 1 formula',
                                     help=_VALUE_FORMULA_HELP),
        'previous_value': fields.text('Fiscal year 2 formula',
                                      help=_VALUE_FORMULA_HELP),
        'negate': fields.boolean(
            'Negate',
            help="Negate the value (change the sign of the balance)"),
        'parent_id': fields.many2one('account.balance.reporting.template.line',
                                     'Parent', ondelete='cascade'),
        'child_ids': fields.one2many('account.balance.reporting.template.line',
                                     'parent_id', 'Children'),
    }

    _defaults = {
        'template_id': lambda self, cr, uid, context: context.get(
            'template_id', None),
        'negate': False,
        'css_class': 'default',
        'sequence': 10,
    }

    _order = "sequence, code"

    _sql_constraints = [
        ('report_code_uniq', 'unique(template_id, code)',
         _("The code must be unique for this report!"))
    ]

    def name_get(self, cr, uid, ids, context=None):
        """
        Redefine the name_get method to show the code in the name
        ("[code] name").
        """
        if context is None:
            context = {}
        res = []
        for item in self.browse(cr, uid, ids, context=context):
            res.append((item.id, "[%s] %s" % (item.code, item.name)))
        return res

    def name_search(self, cr, uid, name, args=[], operator='ilike',
                    context=None, limit=80):
        """
        Redefine the name_search method to allow searching by code.
        """
        if context is None:
            context = {}
        ids = []
        if name:
            ids = self.search(cr, uid, [('code', 'ilike', name)] + args,
                              limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('name', operator, name)] + args,
                                  limit=limit, context=context)
        return self.name_get(cr, uid, ids, context=context)
