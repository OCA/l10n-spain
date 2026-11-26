# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    transaher_barcode = fields.Char(
        string="Transaher 24-Digit Barcode",
        copy=False,
        index=True,
        help=(
            "24-character Code 128 / Interleaved 2 of 5 barcode generated "
            "per Transaher Technical Manual Section 5.2."
        ),
    )
    transaher_sscc = fields.Char(
        string="Transaher SSCC / EAN",
        copy=False,
        index=True,
        help=(
            "Package EAN / SSCC identifier reported by Transaher "
            "wsInformacionTransporte."
        ),
    )
