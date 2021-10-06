# Copyright 2015-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountAsset(models.Model):
    _inherit = "account.asset"

    vat_prorrate_percent = fields.Float()
    vat_prorrate_increment = fields.Float()
