# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    def _clear_tax_id_from_tax_template_cache(self):
        self.env.registry.clear_cache()

    @api.model_create_multi
    def create(self, vals_list):
        """Invalidate company cache that links templates with taxes as
        there are potential new taxes that can match.
        """
        res = super().create(vals_list)
        self._clear_tax_id_from_tax_template_cache()
        return res

    def unlink(self):
        """Invalidate company cache that links templates with taxes for not
        returning a potential invalid tax that has been unlinked.
        """
        res = super().unlink()
        self._clear_tax_id_from_tax_template_cache()
        return res
