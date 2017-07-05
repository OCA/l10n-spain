# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sii_enabled = fields.Boolean(
        related="company_id.sii_enabled", readonly=True,
    )
    sii_simplified_invoice = fields.Boolean(
        string="Simplified invoices in SII?",
        help="Checking this mark, invoices done to this partner will be "
             "sent to SII as simplified invoices."
    )
