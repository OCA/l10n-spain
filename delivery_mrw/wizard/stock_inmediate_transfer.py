# Copyright 2022 ForgeFlow, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockImmediateTransfer(models.TransientModel):
    _inherit = "stock.immediate.transfer"

    mrw_to_address = fields.Html("Address sent to MRW", readonly=True)

    def default_get(self, fields):
        res = super().default_get(fields)
        immediate_line = res.get("immediate_transfer_line_ids", False)
        if immediate_line and len(immediate_line) == 1:
            picking = self.env["stock.picking"].browse(
                immediate_line[0][2]["picking_id"]
            )
            if picking.carrier_id.delivery_type == "mrw":
                mrw_address = picking.carrier_id.mrw_address(
                    picking.partner_id, picking.carrier_id.international_shipping
                )
                res["mrw_to_address"] = self._prepare_html_address(mrw_address)
        return res

    def _prepare_html_address(self, mrw_address):
        l_address = []
        for key in mrw_address:
            if mrw_address[key]:
                l_address.append(
                    "<strong>%s</strong>: %s <br>" % (key, mrw_address[key])
                )
        return "".join(l_address)
