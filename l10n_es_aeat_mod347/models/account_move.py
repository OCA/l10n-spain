# Copyright 2018 PESOL - Angel Moya <info@pesol.es>
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    not_in_mod347 = fields.Boolean(
        "Force not included in 347 report",
        help="If you mark this field, this invoice will not be included in "
        "any AEAT 347 model report.",
        default=False,
    )
