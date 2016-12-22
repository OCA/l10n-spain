# -*- coding: utf-8 -*-
# © 2009 Pexego/Comunitea
# © 2016 Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0).

from openerp import api, fields, models, _


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


class AccountBalanceReportingTemplate(models.Model):
    _name = "account.balance.reporting.template"
    _description = (
        "Account balance report template. It stores the header fields of an "
        "account balance report template, and the linked lines of detail with "
        "the formulas to calculate the accounting concepts of the report.")

    name = fields.Char(string='Name', size=64, required=True, index=True)
    tmpl_type = fields.Selection(
        selection=[('system', 'System'),
                   ('user', 'User')],
        string='Type', default='user', old_name='type')
    report_xml_id = fields.Many2one(
        comodel_name='ir.actions.report.xml', string='Report design',
        ondelete='set null')
    description = fields.Text('Description')
    balance_mode = fields.Selection(
        [('0', 'Debit-Credit'),
         ('1', 'Debit-Credit, reversed with brackets'),
         ('2', 'Credit-Debit'),
         ('3', 'Credit-Debit, reversed with brackets')],
        string='Balance mode', default="0",
        help="Formula calculation mode: Depending on it, the balance is "
             "calculated as follows:\n"
             "Mode 0: debit-credit (default);\n"
             "Mode 1: debit-credit, credit-debit for accounts in brackets;\n"
             "Mode 2: credit-debit;\n"
             "Mode 3: credit-debit, debit-credit for accounts in brackets.")
    line_ids = fields.One2many(
        comodel_name='account.balance.reporting.template.line',
        inverse_name='template_id', string='Lines')

    @api.multi
    def copy(self, default=None):
        """Redefine the copy method to perform it correctly as the line
        structure is a graph.
        """
        line_obj = self.env['account.balance.reporting.template.line']
        # Create the template
        new = self.create({
            'name': '%s*' % self.name,
            'tmpl_type': 'user',  # Copies are always user templates
            'report_xml_id': self.report_xml_id.id,
            'description': self.description,
            'balance_mode': self.balance_mode,
            'line_ids': None,
        })
        # Now create the lines (without parents)
        for line in self.line_ids:
            line_obj.create({
                'template_id': new.id,
                'sequence': line.sequence,
                'css_class': line.css_class,
                'code': line.code,
                'name': line.name,
                'current_value': line.current_value,
                'previous_value': line.previous_value,
                'negate': line.negate,
                'parent_id': False,
                'child_ids': False,
            })
        # Now set the (lines) parents
        for line in self.line_ids:
            if line.parent_id:
                # Search for the copied line
                new_line = line_obj.search([
                    ('template_id', '=', new.id),
                    ('code', '=', line.code),
                ])[:1]
                # Search for the copied parent line
                new_parent_id = line_obj.search([
                    ('template_id', '=', new.id),
                    ('code', '=', line.parent_id.code),
                ])[0]
                # Set the parent
                new_line.parent_id = new_parent_id
        return new


class AccountBalanceReportingTemplateLine(models.Model):
    _name = "account.balance.reporting.template.line"
    _description = (
        "Account balance report template line / Accounting concept template "
        "One line of detail of the balance report representing an accounting "
        "concept with the formulas to calculate its values. ")
    _order = "sequence, code"

    template_id = fields.Many2one(
        comodel_name='account.balance.reporting.template', string='Template',
        ondelete='cascade')
    sequence = fields.Integer(
        string='Sequence', required=True, default=10,
        help="Lines will be sorted/grouped by this field")
    css_class = fields.Selection(
        selection=CSS_CLASSES, string='CSS Class', required=False,
        help="Style-sheet class", default='default')
    code = fields.Char(
        string='Code', size=64, required=True, index=True,
        help="Concept code, may be used on formulas to reference this line")
    name = fields.Char(
        string='Name', size=256, required=True, index=True,
        help="Concept name/description")
    current_value = fields.Text(
        string='Fiscal year 1 formula', help=_VALUE_FORMULA_HELP)
    previous_value = fields.Text(
        string='Fiscal year 2 formula', help=_VALUE_FORMULA_HELP)
    negate = fields.Boolean(
        string='Negate',
        help="Negate the value (change the sign of the balance)")
    parent_id = fields.Many2one(
        comodel_name='account.balance.reporting.template.line',
        string='Parent', ondelete='cascade')
    child_ids = fields.One2many(
        comodel_name='account.balance.reporting.template.line',
        inverse_name='parent_id', string='Children')

    _sql_constraints = [
        ('report_code_uniq', 'unique(template_id, code)',
         _("The code must be unique for this report!"))
    ]

    @api.multi
    def name_get(self):
        """Redefine the name_get method to show the code in the name
        ("[code] name").
        """
        res = []
        for item in self:
            res.append((item.id, "[%s] %s" % (item.code, item.name)))
        return res

    def name_search(self, cr, uid, name, args=None, operator='ilike',
                    context=None, limit=80):
        """Redefine the name_search method to allow searching by code."""
        if context is None:
            context = {}
        if args is None:
            args = []
        ids = []
        if name:
            ids = self.search(cr, uid, [('code', 'ilike', name)] + args,
                              limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('name', operator, name)] + args,
                                  limit=limit, context=context)
        return self.name_get(cr, uid, ids, context=context)
