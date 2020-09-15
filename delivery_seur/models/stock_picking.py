
# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    seur_last_request = fields.Text(
        string="Last SEUR xml request",
        help="Used for issues debugging",
        copy=False,
        readonly=True,
    )
    seur_last_response = fields.Text(
        string="Last SEUR xml response",
        help="Used for issues debugging",
        copy=False,
        readonly=True,
    )
