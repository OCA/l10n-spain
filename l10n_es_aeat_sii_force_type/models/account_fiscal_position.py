# © 2019 FactorLibre - Daniel Duque <daniel.duque@factorlibre.com>
# © 2024 FactorLibre - Alejandro Ji Cheung <alejandro.jicheung@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    @api.model
    def _get_selection_sii_forced_communication_type(self):
        invoice_fields = self.env["account.move"].fields_get(
            allfields=["sii_force_communication_type"]
        )
        return invoice_fields["sii_force_communication_type"]["selection"]

    sii_allow_force_communication_type = fields.Boolean(
        "Allow force communication type on invoices"
    )

    sii_forced_communication_type = fields.Selection(
        string="Default communication type",
        selection="_get_selection_sii_forced_communication_type",
    )
