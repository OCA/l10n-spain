# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    @api.model
    def _l10n_es_regime_code_labels(self):
        """Add the SII registration keys that the shared core catalog lacks."""
        labels = super()._l10n_es_regime_code_labels()
        labels.update(
            {
                "06": self.env._("06 - Group of entities in VAT (advanced level)"),
                # Only for the invoices registered in the first half of 2017
                "16_sale": self.env._("16 - First half of 2017"),
                "14_purchase": self.env._("14 - First half of 2017"),
            }
        )
        return labels
