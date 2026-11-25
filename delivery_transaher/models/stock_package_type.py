# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

from .transaher_master_data import TRANSAHER_PACKAGING_CODES


class StockPackageType(models.Model):
    _inherit = "stock.package.type"

    package_carrier_type = fields.Selection(
        selection_add=[("transaher", "Transaher")],
        ondelete={"transaher": "set default"},
    )
    transaher_packaging_code = fields.Selection(
        selection=TRANSAHER_PACKAGING_CODES,
        string="Transaher Packaging Type",
        default="BUL",
        help=(
            "Package/pallet classification for Transaher shipments "
            "(BUL = Parcel, CAJ = Box, EUR = Euro Pallet, PAL = Pallet)."
        ),
    )

    @api.onchange("package_carrier_type", "transaher_packaging_code")
    def _onchange_transaher_packaging_code(self):
        if self.package_carrier_type == "transaher" and self.transaher_packaging_code:
            self.shipper_package_code = self.transaher_packaging_code

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if (
                vals.get("package_carrier_type") == "transaher"
                and vals.get("transaher_packaging_code")
                and not vals.get("shipper_package_code")
            ):
                vals["shipper_package_code"] = vals["transaher_packaging_code"]
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("transaher_packaging_code") and "shipper_package_code" not in vals:
            for rec in self:
                if (
                    vals.get("package_carrier_type") or rec.package_carrier_type
                ) == "transaher":
                    rec.shipper_package_code = vals["transaher_packaging_code"]
        return super().write(vals)
