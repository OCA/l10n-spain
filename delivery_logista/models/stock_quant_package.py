# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    logista_barcode = fields.Char(
        string="Logista 34-Digit Barcode",
        copy=False,
        index=True,
        help="34-character Code 128 barcode generated for Logista Parcel labels.",
    )
