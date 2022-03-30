# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCountry(models.Model):
    _inherit = "res.country"

    country_vat = fields.Char(
        string="VAT",
        help="Your company's VAT number in this country",
        company_dependent=True,
    )
