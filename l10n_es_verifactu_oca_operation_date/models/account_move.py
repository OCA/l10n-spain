# Copyright 2026 Ozono Multimedia - Iván Antón
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_verifactu_invoice_dict_out(self):
        """Add operation date field to VERIFACTU invoice dict when applicable."""
        res = super()._get_verifactu_invoice_dict_out()
        inv_dict = res.get("RegistroAlta", {})

        # Include FechaOperacion only when operation date differs from invoice date
        if self.date and self.date != self.invoice_date:
            inv_dict["FechaOperacion"] = self._get_verifactu_date(self.date)

        return res

    def _check_verifactu_configuration(self, suffixes=None):
        """Validate that operation date is not greater than invoice date."""
        if suffixes is None:
            suffixes = []

        # Validate operation date constraint
        if self.date and self.date > self.invoice_date:
            suffixes.append(
                _("- The operation date cannot be greater than the invoice date.")
            )

        return super()._check_verifactu_configuration(suffixes=suffixes)
