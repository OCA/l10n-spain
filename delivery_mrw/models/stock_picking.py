# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


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

    def _check_destination_country(self, international):
        country = self.partner_id.country_id
        if (country.code == "ES" and international) or (
            country.code != "ES" and not international
        ):
            raise UserError(
                _(
                    "Destination country doesn't match carrier service type,"
                    " international = %s and partner country = %s"
                )
                % (international, country.name)
            )
