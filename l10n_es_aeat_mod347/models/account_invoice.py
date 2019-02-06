from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    not_in_mod347 = fields.Boolean(
        "Not included in 347 report",
        help="If you mark this field, this invoice will not be included in "
             "any AEAT 347 model report.", default=False,
    )
