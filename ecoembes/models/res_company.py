# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    ecoembes_inscription = fields.Char(string="Ecoembes Inscription")
    ecoembes_partner_member = fields.Char(string="Ecoembes Partner Member")
