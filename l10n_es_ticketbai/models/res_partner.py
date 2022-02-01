# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tbai_simplified_invoice = fields.Boolean(
        string="Simplified invoices in TBAI?",
        help="Checking this mark, invoices done to this partner will be "
        "sent to TBAI as simplified invoices.",
    )
    tbai_anonymous_simplified_invoice = fields.Boolean(
        string="Anonymous simplified invoices in TBAI?",
        help="Checking this mark, invoices done to this partner will be "
        "sent to TBAI as simplified invoices whitout customer.",
    )
