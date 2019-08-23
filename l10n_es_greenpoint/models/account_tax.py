# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields
from odoo.tools.safe_eval import safe_eval

class AccountTaxPython(models.Model):
    _inherit = "account.tax"

    is_uom_needed = fields.Boolean(
        string = "Is UOM Needed for calculation?")

    def _compute_amount(self, base_amount, price_unit, quantity = 1.0,
                        product = None, partner = None):
        self.ensure_one()
        if self.is_uom_needed:
            uom = self.env.context.get('uom')
            if not uom:
                factor = 1
            else:
                factor = uom.factor_inv
            company = self.env.user.company_id
            localdict = {'base_amount': base_amount, 'price_unit':price_unit,
                         'quantity': quantity, 'product':product,
                         'partner':partner, 'company': company,
                         'factor': factor}
            safe_eval(self.python_compute, localdict, mode="exec", nocopy=True)
            return localdict['result']
        return super(AccountTaxPython, self)._compute_amount(
            base_amount, price_unit, quantity, product, partner)

class AccountTaxTemplatePython(models.Model):
    _inherit = 'account.tax.template'

    is_uom_needed = fields.Boolean(
        string = "Is UOM Needed for calculation?"
    )

    def _get_tax_vals(self, company, tax_template_to_tax):
        """ This method generates a dictionnary of all the values for the tax that will be created.
        """
        self.ensure_one()
        res = super(AccountTaxTemplatePython, self)._get_tax_vals(
            company, tax_template_to_tax)
        res['is_uom_needed'] = self.is_uom_needed
        return res