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
Account balance report templates

Generic account balance report template that will be used to define
accounting concepts with formulas to calculate its values/balance.
Designed following the needs of the Spanish/Spain localization.
"""
__author__ = "Borja López Soilán (Pexego) - borjals@pexego.es"


from osv import fields, osv
import re
import time
from tools.translate import _

################################################################################
# CSS classes for the account lines
################################################################################

CSS_CLASSES = [('default','Default'),('l1', 'Level 1'), ('l2', 'Level 2'),
                ('l3', 'Level 3'), ('l4', 'Level 4'), ('l5', 'Level 5')]

################################################################################
# Account balance report template (document/header)
################################################################################

class account_balance_report_template(osv.osv):
    """
    Account balance report template.
    It stores the header fields of an account balance report template,
    and the linked lines of detail with the formulas to calculate
    the accounting concepts of the report.
    """

    _name = "account.balance.report.template"

    _columns = {
        # Report template name
        'name': fields.char('Name', size=64, required=True, select=True),
        # Type (system = not editable by the user [updated from XML files])
        'type': fields.selection([('system','System'),('user','User')], 'Type'),
        # Report design
        'report_xml_id': fields.many2one('ir.actions.report.xml', 'Report design', ondelete='set null'),
        # Description
        'description': fields.text('Description'),
    }

    _defaults = {
        # New templates are 'user' editable by default
        'type': lambda *a: 'user'
    }

account_balance_report_template()



################################################################################
# Account balance report template line of detail (accounting concept template)
################################################################################

class account_balance_report_template_line(osv.osv):
    """
    Account balance report template line / Accounting concept template
    One line of detail of the balance report representing an accounting
    concept with the formulas to calculate its values.
    The accounting concepts follow a parent-children hierarchy.
    """

    _name = "account.balance.report.template.line"

    _columns = {
        # Parent report of this line
        'report_id': fields.many2one('account.balance.report.template', 'Template', ondelete='cascade'),

        # Order sequence, it's also used for grouping into sections, that's why it is a char
        'sequence': fields.char('Sequence', size=32, required=False),
        # CSS class, used when printing to set the style of the line
        'css_class': fields.selection(CSS_CLASSES, 'CSS Class', required=False),

        # Concept official code (as specified by normalized models, will be used when printing)
        'code': fields.char('Code', size=64, required=True, select=True),
        # Concept official name (will be used when printing)
        'name': fields.char('Name', size=256, required=True, select=True),
        # Concept value formula in this fiscal year
        'current_value': fields.text('Fiscal year 1 formula'),
        # Concept value on the previous fiscal year
        'previous_value': fields.text('Fiscal year 2 formula'),

        # Parent accounting concept
        'parent_id': fields.many2one('account.balance.report.template.line', 'Parent', ondelete='cascade'),
        # Children accounting concepts
        'child_ids': fields.one2many('account.balance.report.template.line', 'parent_id', 'Children'),
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


account_balance_report_template_line()


class account_balance_report_template_withlines(osv.osv):
    """
    Extend the 'account balance report template' to add a link to its
    lines of detail.
    """

    _inherit = "account.balance.report.template"

    _columns = {
        'line_ids': fields.one2many('account.balance.report.template.line', 'report_id', 'Lines'),
    }

account_balance_report_template_withlines()




