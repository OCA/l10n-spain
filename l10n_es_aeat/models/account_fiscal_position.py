# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# Copyright 2024 Aures TIC - Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    aeat_active = fields.Boolean(
        string="AEAT Active",
        copy=False,
        default=True,
        help="Enable AEAT communication for this fiscal position?",
    )
