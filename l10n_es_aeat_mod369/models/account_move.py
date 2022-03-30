# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    origin_country_id = fields.Many2one(
        string="Origin country", comodel_name="res.country"
    )
    fp_outside_spain = fields.Boolean(
        string="Outside of Spain", related="fiscal_position_id.outside_spain"
    )
