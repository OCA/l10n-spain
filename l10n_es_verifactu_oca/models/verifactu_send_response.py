# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class VerifactuSendResponse(models.Model):
    _name = "verifactu.send.response"
    _description = "Verifactu Send Response"

    header = fields.Text()
    invoice_data = fields.Text()
    response = fields.Text()
    verifactu_csv = fields.Text()
