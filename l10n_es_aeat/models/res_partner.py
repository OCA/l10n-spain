# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    simplified_invoice = fields.Boolean(
        string="Simplified invoices in SII or VAT book?",
        help="Checking this mark, invoices done to this partner will be "
             "sent to SII as simplified invoices or export to VAT book.",
        oldname="sii_simplified_invoice",
    )
