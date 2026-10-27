# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# Copyright 2023 Javier Colmenero - (https://javier@comunitea.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    company_plastic_acquirer = fields.Boolean(string="Plastic Acquirer", default=True)
    company_plastic_manufacturer = fields.Boolean(
        string="Plastic Manufacturer", default=False
    )
