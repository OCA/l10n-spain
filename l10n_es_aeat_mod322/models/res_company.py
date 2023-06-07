# Copyright 2022 QubiQ - Jan Tugores
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    group_number = fields.Char(string="Nº Grupo", help="Número de grupo de la empresa.")
