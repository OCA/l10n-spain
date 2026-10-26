# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _get_aeat_taxes_map(self, codes, date):
        """Replicates the same logic as ``l10n_es_aeat_sii_oss`` for POS orders.
        """
        taxes = super()._get_aeat_taxes_map(codes, date)
        if any(x in ["SFENS", "NotIncludedInTotal"] for x in codes):
            taxes |= self.env["account.tax"].search(
                [
                    ("oss_country_id", "!=", False),
                    ("company_id", "=", self.company_id.id),
                ]
            )
        return taxes
