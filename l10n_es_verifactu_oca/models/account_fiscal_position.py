# Copyright 2024 Aures TIC - Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    verifactu_enabled = fields.Boolean(
        related="company_id.verifactu_enabled",
        readonly=True,
    )
