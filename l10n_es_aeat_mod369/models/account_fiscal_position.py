# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    oss_regimen = fields.Selection(
        string="OSS Regimen",
        selection=[("union", "Union"), ("exterior", "Exterior"), ("import", "Import")],
        help="Used to specify which page it will be used in the 369 model",
    )
    outside_spain = fields.Boolean(
        string="Outside of Spain",
        help="This field is to differentiate moves for the 369 model (union)",
    )
