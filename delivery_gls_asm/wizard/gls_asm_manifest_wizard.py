# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError
from ..models.gls_asm_request import GlsAsmRequest


class DeliverySeurManifiestoWizard(models.TransientModel):
    _name = "gls.asm.minifest.wizard"
    _description = "Get the GLS Manifest for the given date range"

    date_from = fields.Date(
        required=True,
        default=fields.Date.context_today,
    )
    carrier_id = fields.Many2one(
        string="GLS Service",
        comodel_name="delivery.carrier",
        domain=[('delivery_type', '=', 'gls_asm')],
        required=True,
    )

    def get_manifest(self):
        """List of shippings for the given dates as GLS provides them"""
        gls_request = GlsAsmRequest(self.carrier_id._gls_asm_uid())
        manifest_data = gls_request._get_manifest(self.date_from)
        if not manifest_data:
            raise UserError(_(
                "It wasn't possible to get the manifest. Maybe there aren't"
                "deliveries for the selected date."))
        datas = {
            "ids": self.env.context.get('active_ids', []),
            "model": "gls.asm.minifest.wizard",
            "deliveries": manifest_data,
            "date_from": self.date_from,
            "company_name": self.carrier_id.company_id.name,
        }
        return self.env.ref(
            "delivery_gls_asm.gls_asm_manifest_report"
        ).report_action(self, data=datas)
