# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    tax_reduction_type = fields.Selection(
        string="Tax type", selection=[("S", "Standard"), ("R", "Reduced")]
    )
    service_type = fields.Selection(
        string="Service type",
        selection=[("goods", "Goods"), ("services", "Services")],
        default="goods",
    )
