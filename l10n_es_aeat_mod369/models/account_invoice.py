from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    origin_country_id = fields.Many2one(
        string="Origin country", comodel_name="res.country"
    )
    fp_outside_spain = fields.Boolean(
        string="Outside of Spain", related="fiscal_position_id.outside_spain"
    )
