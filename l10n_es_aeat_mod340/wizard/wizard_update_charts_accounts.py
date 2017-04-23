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

from openerp import _, models


class WizardUpdateChartsAccounts(models.TransientModel):
    _inherit = 'wizard.update.charts.accounts'

    def _is_different_tax_code(self, tax_code, tax_code_template,
                               mapping_tax_codes):
        notes = super(WizardUpdateChartsAccounts, self)._is_different_tax_code(
            tax_code, tax_code_template, mapping_tax_codes)
        if tax_code.mod340 != tax_code_template.mod340:
            notes += _("The 340 model field is different.\n")
        return notes

    def _prepare_tax_code_vals(self, tax_code_template, mapping_tax_codes):
        res = super(WizardUpdateChartsAccounts, self)._prepare_tax_code_vals(
            tax_code_template, mapping_tax_codes)
        res['mod340'] = tax_code_template.mod340
        return res

    def _is_different_tax(self, tax, tax_template, mapping_taxes,
                          mapping_tax_codes, mapping_accounts):
        notes = super(WizardUpdateChartsAccounts, self)._is_different_tax(
            tax, tax_template, mapping_taxes, mapping_tax_codes,
            mapping_accounts)
        if tax.is_340_reserve_charge != tax_template.is_340_reserve_charge:
            notes += _("The field is 340 reverse charge is different.\n")
        return notes

    def _prepare_tax_vals(self, tax_template, mapping_tax_codes,
                          mapping_taxes):
        res = super(WizardUpdateChartsAccounts, self)._prepare_tax_vals(
            tax_template, mapping_tax_codes, mapping_taxes)
        res['is_340_reserve_charge'] = tax_template.is_340_reserve_charge
        return res
