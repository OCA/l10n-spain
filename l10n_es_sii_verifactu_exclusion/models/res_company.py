# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.onchange("sii_enabled")
    def _onchange_sii_enabled(self):
        if self.sii_enabled and self.verifactu_enabled:
            raise ValidationError(
                _(
                    "SII has been disabled because it cannot be "
                    "enabled together with Verifactu."
                )
            )

    @api.onchange("verifactu_enabled")
    def _onchange_verifactu_enabled(self):
        if self.verifactu_enabled and self.sii_enabled:
            raise ValidationError(
                _(
                    "Verifactu has been disabled because it cannot be "
                    "enabled together with SII."
                )
            )

    @api.constrains("sii_enabled", "verifactu_enabled")
    def _check_sii_verifactu_exclusivity(self):
        for record in self:
            if record.sii_enabled and record.verifactu_enabled:
                raise ValidationError(
                    _(
                        "You cannot enable both SII and Verifactu at the same time. "
                        "Please disable one of them."
                    )
                )
