# Copyright 2024 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    colegio_concertado = fields.Boolean(
        string="College concerted",
        default=False,
    )
