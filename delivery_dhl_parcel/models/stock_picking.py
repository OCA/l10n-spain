# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64

from odoo import _, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    dhl_parcel_shipment_held = fields.Boolean(string="DHL Parcel shipment on hold")

    # TODO: The label_format parameter is not used and can be removed.
    def dhl_parcel_get_label(self, label_format="pdf"):
        """Get DHL Parcel Label for this picking expedition"""
        self.ensure_one()
        tracking_ref = self.carrier_tracking_ref
        if self.delivery_type != "dhl_parcel" or not tracking_ref:
            return
        label = base64.b64decode(self.carrier_id.dhl_parcel_get_label(tracking_ref))
        label_format = self.carrier_id.dhl_parcel_label_format.lower()
        label_name = "dhl_parcel_{}.{}".format(
            tracking_ref, "txt" if label_format == "zpl" else "pdf"
        )
        self.message_post(
            body=(_("DHL Parcel label for %s") % tracking_ref),
            attachments=[(label_name, label)],
        )
        # We return label in case it wants to be printed in an inheritance
        return label

    def dhl_parcel_toggle_hold_shipment(self):
        """Toggle between holding and releasing the DHL Parcel shipment"""
        self.ensure_one()
        tracking_ref = self.carrier_tracking_ref
        if self.delivery_type != "dhl_parcel" or not tracking_ref:
            return
        message = ""
        carrier = self.carrier_id
        if self.dhl_parcel_shipment_held:
            self.dhl_parcel_shipment_held = not carrier.dhl_parcel_release_shipment(
                tracking_ref
            )
            message = _("Released shipment for {}").format(tracking_ref)
        else:
            self.dhl_parcel_shipment_held = carrier.dhl_parcel_hold_shipment(
                tracking_ref
            )
            message = _("Held shipment for {}").format(tracking_ref)
        self.message_post(body=message)
