# Copyright 2021 FactorLibre - Rodrigo Bonilla <rodrigo.bonilla@factorlibre.com>
# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_aeat_taxes_map(self, codes, date):
        """Inject OSS taxes when querying not subjected invoices."""
        taxes = super()._get_aeat_taxes_map(codes, date)
        if any([x in ["SFENS", "NotIncludedInTotal"] for x in codes]):
            taxes |= self.env["account.tax"].search(
                [
                    ("oss_country_id", "!=", False),
                    ("company_id", "=", self.company_id.id),
                ]
            )
        return taxes
