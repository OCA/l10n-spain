# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    spfe_registration_key_id = fields.Many2one(
        comodel_name="l10n.es.spfe.registration.key",
        string="SPFE Default Regime Key",
        help="Default SPFE regime key applied to invoice lines using this fiscal "
        "position.",
    )
