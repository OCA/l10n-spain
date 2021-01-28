# Copyright 2021 Enrique Martin <enriquemartin@digital5.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AeatTaxAgency(models.Model):
    _name = "aeat.tax.agency"
    _description = "Aeat Tax Agency"

    name = fields.Char(string="Name", required=True)
