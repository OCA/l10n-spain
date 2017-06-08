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

from openerp import models, _


class WizardUpdateChartsAccounts(models.TransientModel):
    _inherit = 'wizard.update.charts.accounts'

    def _is_different_tax_code(self, tax_code, tax_code_template,
                               mapping_tax_codes):
        notes = super(WizardUpdateChartsAccounts, self)._is_different_tax_code(
            tax_code, tax_code_template, mapping_tax_codes)
        if tax_code.prorrata_tax_type != tax_code_template.prorrata_tax_type:
            notes += _("The type of prorrata tax is different.\n")
        return notes

    def _prepare_tax_code_vals(self, tax_code_template, mapping_tax_codes):
        res = super(WizardUpdateChartsAccounts, self)._prepare_tax_code_vals(
            tax_code_template, mapping_tax_codes)
        res['prorrata_tax_type'] = tax_code_template.prorrata_tax_type
        return res
