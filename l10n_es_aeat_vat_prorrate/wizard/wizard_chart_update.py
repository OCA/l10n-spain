# -*- coding: utf-8 -*-
# © 2017 Praxya - Carlos Alba
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models


class WizardUpdateChartsAccounts(models.TransientModel):
    _inherit = 'wizard.update.charts.accounts'

    def _prepare_tax_code_vals(self, tax_code_template, mapping_tax_codes):
        """
            Completes the values of the tax code, with the new bool value for
            the special prorrate taxes codes.
        """
        vals = super(WizardUpdateChartsAccounts, self)._prepare_tax_code_vals(
            tax_code_template,
            mapping_tax_codes)
        vals['is_special_prorrate_code'] = \
            tax_code_template.is_special_prorrate_code
        return vals
