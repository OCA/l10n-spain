# Copyright 2020 Creu Blanca

from odoo import fields, models


class CountryState(models.Model):
    _inherit = "res.country.state"

    aeat_code = fields.Char()
