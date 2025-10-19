# Copyright 2021 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class TicketBAIVATRegimeKey(models.Model):
    _inherit = "tbai.vat.regime.key"

    type = fields.Selection(
        selection=[("sale", "Sale"), ("purchase", "Purchase")],
        required=True,
    )
