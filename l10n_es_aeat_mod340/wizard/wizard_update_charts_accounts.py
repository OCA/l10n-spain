# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################

from openerp.osv import orm
from openerp.tools.translate import _


class WizardUpdateChartsAccounts(orm.TransientModel):
    _inherit = 'wizard.update.charts.accounts'

    def _is_different_tax_code(self, cr, uid, wizard, tax_code,
                               tax_code_template, tax_code_template_mapping,
                               context=None):
        notes = super(WizardUpdateChartsAccounts, self)._is_different_tax_code(
            cr, uid, wizard, tax_code, tax_code_template,
            tax_code_template_mapping, context=context)
        if tax_code.mod340 != tax_code_template.mod340:
            notes += _("The Mod 340 field is different.\n")
        return notes

    def _prepare_tax_code_vals(self, cr, uid, wizard, tax_code_template,
                               tax_code_template_mapping, context=None):
        res = super(WizardUpdateChartsAccounts, self)._prepare_tax_code_vals(
            cr, uid, wizard, tax_code_template, tax_code_template_mapping,
            context=context)
        res['mod340'] = tax_code_template.mod340
        return res
