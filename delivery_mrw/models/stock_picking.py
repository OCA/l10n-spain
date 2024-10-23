# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def mrw_get_label(self):
        self.ensure_one()
        tracking_ref = self.carrier_tracking_ref
        if self.delivery_type != "mrw" or not tracking_ref:
            return
        label = self.carrier_id.mrw_get_label(tracking_ref, self)
        label_name = "mrw_label_{}.pdf".format(tracking_ref)
        body = _("MRW Shipping Label:")
        attachment = []
        if label["EtiquetaFile"]:
            attachment = [
                (
                    label_name,
                    label["EtiquetaFile"],
                )
            ]
        self.message_post(
            body=body,
            attachments=attachment,
        )
        return label
