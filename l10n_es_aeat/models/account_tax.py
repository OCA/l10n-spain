# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    aeat_equivalent_tax_id = fields.Many2one(
        comodel_name="account.tax",
        string="Equivalent Tax (for AEAT mapping purposes)",
        help="This field is for manually created taxes in order to allow to map them"
        " for AEAT reports",
    )

    def _clear_tax_id_from_tax_template_cache(self):
        Company = self.env["res.company"]
        Company._get_tax_id_from_tax_template.clear_cache(Company)

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

    def copy_data(self, default=None):
        """When duplicating a tax, if it does not contain an equivalent tax,
        takes itself as base.
        """
        vals_list = super().copy_data(default=default)
        for record, vals in zip(self, vals_list, strict=False):
            if not vals.get("aeat_equivalent_tax_id"):
                vals["aeat_equivalent_tax_id"] = (
                    record.aeat_equivalent_tax_id.id or record.id
                )
        return vals_list
