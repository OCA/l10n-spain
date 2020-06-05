# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # ASM API has two references for each delivery. This one is needed
    # for some operations like getting the label
    gls_asm_public_tracking_ref = fields.Char(
        string="GLS Barcode",
        readonly=True,
        copy=False,
    )

    def gls_asm_get_label(self):
        """Get GLS Label for this picking expedition"""
        self.ensure_one()
        if (self.delivery_type != "gls_asm" or not
                self.gls_asm_public_tracking_ref):
            return
        pdf = self.carrier_id.gls_asm_get_label(
            self.gls_asm_public_tracking_ref)
        label_name = "gls_{}.pdf".format(self.gls_asm_public_tracking_ref)
        self.message_post(
            body=(_("GLS label for %s") % self.gls_asm_public_tracking_ref),
            attachments=[(label_name, pdf)],
        )
