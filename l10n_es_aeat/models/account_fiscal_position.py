# -*- coding: utf-8 -*-
from openerp import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    partner_identification_type = fields.Selection(
        selection=[('1', 'National'), ('2', 'Intracom'), ('3', 'Export')],
        string="Partner Identification Type",
        help="Currently, this field is used for the VAT book and for the SII.",
        oldname="sii_partner_identification_type",
    )
