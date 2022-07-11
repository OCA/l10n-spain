# Copyright 2022 Trey, Kilobytes de Soluciones - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    property_account_refund_in_id = fields.Many2one(
        comodel_name="account.account",
        company_dependent=True,
        string="Refund In Account",
        domain=[("deprecated", "=", False)],
        help="Keep this field empty to use the default value from the product "
             "category.",
    )
    property_account_refund_out_id = fields.Many2one(
        comodel_name="account.account",
        company_dependent=True,
        string="Refund Out Account",
        domain=[("deprecated", "=", False)],
        help="Keep this field empty to use the default value from the product "
             "category.",
    )
