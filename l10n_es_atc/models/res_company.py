from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    atc_public_way = fields.Char("Public Way")
