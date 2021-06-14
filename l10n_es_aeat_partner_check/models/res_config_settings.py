# Copyright 2019 Acysos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vat_check_aeat = fields.Boolean(
        related="company_id.vat_check_aeat",
        readonly=False,
        string="Verify AEAT Partner Data",
    )
