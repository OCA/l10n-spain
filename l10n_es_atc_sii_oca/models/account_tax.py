# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError

# Exemption causes of the SII of the Canary tax agency that the AEAT has not
IGIC_ONLY_EXEMPT_REASONS = ("E7", "E8")

# Registration keys of the purchases of the SII of the Canary tax agency, which
# are numbered differently than the sale ones (17 on sales is 15 on purchases)
IGIC_PURCHASE_REGIME_CODES = [
    "15_igic_purchase",
    "16_igic_purchase",
    "17_igic_purchase",
]


class AccountTax(models.Model):
    _inherit = "account.tax"

    l10n_es_exempt_reason = fields.Selection(
        selection_add=[
            ("E7", "Art. 110 Law 4/2012 (IGIC)"),
            ("E8", "Others (IGIC)"),
        ],
        ondelete={"E7": "set null", "E8": "set null"},
        help="On the IGIC taxes, the exemption causes of the SII of the Canary "
        "tax agency, which are not the ones of the AEAT: E1 art. 50 Law 4/2012 "
        "(retail traders), E2 art. 11 Law 20/1991 (exports), E3 art. 12 Law "
        "20/1991 (operations assimilated to exports), E4 art. 13 Law 20/1991, "
        "E5 art. 25 Law 19/1994, E6 art. 47 Law 19/1994 (Canary Islands "
        "Special Zone), E7 art. 110 Law 4/2012 and E8 others.",
    )

    @api.constrains("l10n_es_exempt_reason", "l10n_es_applicability")
    def _check_l10n_es_atc_exempt_reason(self):
        for tax in self:
            if (
                tax.l10n_es_exempt_reason in IGIC_ONLY_EXEMPT_REASONS
                and tax.l10n_es_applicability != "03"
            ):
                raise ValidationError(
                    self.env._(
                        "The exemption causes E7 and E8 only exist for the IGIC: "
                        "the tax %(tax)s must have the IGIC applicability.",
                        tax=tax.display_name,
                    )
                )

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
