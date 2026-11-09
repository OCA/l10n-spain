# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

# Registration keys of the purchases of the SII of the Canary tax agency, which
# are numbered differently than the sale ones (17 on sales is 15 on purchases)
IGIC_PURCHASE_REGIME_CODES = [
    "15_igic_purchase",
    "16_igic_purchase",
    "17_igic_purchase",
]


class AccountTax(models.Model):
    _inherit = "account.tax"

    @api.model
    def _l10n_es_regime_code_labels(self):
        labels = super()._l10n_es_regime_code_labels()
        labels.update(
            {
                "15_igic_purchase": self.env._(
                    "15 - Special regime for retail traders"
                ),
                "16_igic_purchase": self.env._(
                    "16 - Special regime for small businesses or professionals"
                ),
                "17_igic_purchase": self.env._(
                    "17 - Exempt domestic operations (Art. 25, Law 19/1994)"
                ),
            }
        )
        return labels
