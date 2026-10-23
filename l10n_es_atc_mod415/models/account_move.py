# Copyright 2018 PESOL - Angel Moya <info@pesol.es>
# Copyright 2019 Tecnativa - Pedro M. Baeza
# Copyright 2014-2023 Binhex - Nicolás Ramos (http://binhex.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    not_in_mod415 = fields.Boolean(
        "Force not included in 415 report",
        help="If you mark this field, this invoice will not be included in "
        "any ATC 415 model report.",
        default=False,
    )
