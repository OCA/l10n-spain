# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from .account_tax import IGIC_PURCHASE_REGIME_CODES


class ResCompany(models.Model):
    _inherit = "res.company"

    def _l10n_es_regime_available_codes(self, use, applicability=None):
        codes = super()._l10n_es_regime_available_codes(
            use, applicability=applicability
        )
        if self.sii_enabled and use == "purchase" and applicability == "03":
            codes = list(codes) + IGIC_PURCHASE_REGIME_CODES
        return codes
