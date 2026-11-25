# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

from .logista_master_data import LOGISTA_PACKAGE_KINDS


class StockPackageType(models.Model):
    _inherit = "stock.package.type"

    package_carrier_type = fields.Selection(
        selection_add=[("logista", "Logista Parcel")],
        ondelete={"logista": "set default"},
    )
    logista_package_kind = fields.Selection(
        selection=LOGISTA_PACKAGE_KINDS,
        string="Logista Handling Unit Type",
        default="parcel",
        help=(
            "Classifies this package type as a Parcel (Bulto) or Pallet (Palet) "
            "for Logista Parcel labels and mixed shipments (MixShipment)."
        ),
    )

    @api.onchange("package_carrier_type", "logista_package_kind")
    def _onchange_logista_package_kind(self):
        if (
            self.package_carrier_type == "logista"
            and self.logista_package_kind
            and not self.shipper_package_code
        ):
            self.shipper_package_code = self.logista_package_kind.upper()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if (
                vals.get("package_carrier_type") == "logista"
                and vals.get("logista_package_kind")
                and not vals.get("shipper_package_code")
            ):
                vals["shipper_package_code"] = vals["logista_package_kind"].upper()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("logista_package_kind") and "shipper_package_code" not in vals:
            for rec in self:
                if (
                    vals.get("package_carrier_type") or rec.package_carrier_type
                ) == "logista":
                    rec.shipper_package_code = vals["logista_package_kind"].upper()
        return super().write(vals)
