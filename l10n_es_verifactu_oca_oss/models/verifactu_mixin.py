# Copyright 2025 Factor Libre - Almudena de La Puente <almudena.delapuente@factorlibre.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class VerifactuMixin(models.AbstractModel):
    _inherit = "verifactu.mixin"

    @api.model
    def _get_verifactu_taxes_map(self, codes, date):
        """Inject OSS taxes when querying not subjected invoices."""
        taxes = super()._get_verifactu_taxes_map(codes, date)
        if any([map_code == "N2" for map_code in codes]):
            taxes |= self.env["account.tax"].search(
                [
                    ("oss_country_id", "!=", False),
                    ("company_id", "=", self.company_id.id),
                ]
            )
        return taxes
