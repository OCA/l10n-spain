# Copyright 2021 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    lroe_simplified_invoice = fields.Boolean(
        string="Simplified invoices in LROE?",
        help="Checking this mark, invoices done to this partner will be "
        "sent to LROE as simplified invoices.",
    )
