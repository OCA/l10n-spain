# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


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
        domain=[("delivery_type", "=", "gls_asm")],
        required=True,
    )

    def get_manifest_domain(self):
        return [
            ("carrier_id", "=", self.carrier_id.id),
            ("carrier_tracking_ref", "!=", False),
            ("state", "=", "done"),
            ("date_done", ">=", self.date_from),
        ]

    def get_manifest(self):
        pickings = self.env["stock.picking"].search(
            self.get_manifest_domain(), order="priority desc, date_done asc"
        )
        if not pickings:
            raise UserError(
                _(
                    "It wasn't possible to get the manifest. Maybe there aren't"
                    "deliveries for the selected date."
                )
            )
        manifest_data = []
        for picking in pickings:
            manifest_data.append(
                {
                    "codexp": picking.carrier_tracking_ref,
                    "nombre_dst": picking.partner_id.name,
                    "cp_dst": picking.partner_id.zip,
                    "localidad_dst": picking.partner_id.city,
                    "kgs": picking.shipping_weight,
                    "bultos": picking.number_of_packages,
                }
            )
        if isinstance(manifest_data, dict):
            manifest_data = [manifest_data]
        datas = {
            "ids": self.env.context.get("active_ids", []),
            "model": "gls.asm.minifest.wizard",
            "deliveries": manifest_data,
            "date_from": self.date_from,
            "company_name": self.carrier_id.company_id.name,
        }
        return self.env.ref("delivery_gls_asm.gls_asm_manifest_report").report_action(
            self, data=datas
        )
