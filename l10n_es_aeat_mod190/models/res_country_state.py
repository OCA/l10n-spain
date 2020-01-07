# Copyright 2020 Creu Blanca

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.country.state'

    aeat_code = fields.Char()
