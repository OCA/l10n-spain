# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    tractor_license_plate = fields.Char(
        string="Main vehicle or tractor licence plate",
        size=8,
    )
    trailer_license_plate = fields.Char(
        string="Trailer or semi-trailer licence plate",
        size=8,
    )
    special_authorization = fields.Text(
        string="Special traffic authorisations",
    )
    deca_access_token = fields.Text(
        string="Security access token to share url",
    )
    carrier_contact_id = fields.Many2one(
        comodel_name="res.partner",
        string="Carrier contact",
        help="Carrier contact whose details are printed on the DeCA",
        compute="_compute_carrier_contact_id",
        store=True,
        readonly=False,
    )
    special_authorization_history = fields.Text(
        string="Special authorisation history",
        copy=False,
        readonly=True,
    )
    tractor_license_plate_history = fields.Text(
        string="Tractor licence plate history",
        copy=False,
        readonly=True,
    )
    trailer_license_plate_history = fields.Text(
        string="Trailer licence plate history",
        copy=False,
        readonly=True,
    )
    deca_version = fields.Integer(
        string="DeCA Version",
        default=0,
        copy=False,
        readonly=True,
    )
    deca_first_version_date = fields.Datetime(
        string="DeCA First Version Date",
        copy=False,
        readonly=True,
    )
    deca_content_hash = fields.Char(
        string="DeCA Content Hash",
        copy=False,
        readonly=True,
    )

    @api.depends("carrier_id", "carrier_id.carrier_contact_id")
    def _compute_carrier_contact_id(self):
        for rec in self:
            rec.carrier_contact_id = (
                rec.carrier_id.carrier_contact_id or rec.carrier_contact_id
            )

    def _get_deca_hash(self):
        self.ensure_one()
        data = (
            f"{self.name}{self.tractor_license_plate}{self.trailer_license_plate}"
            f"{self.special_authorization}{self.carrier_id.id}"
            f"{self.carrier_contact_id.id}{self.state}"
        )
        data += (
            f"{self.partner_id.id}{self.picking_type_id.warehouse_id.partner_id.id}"
            f"{self.company_id.id}"
        )
        data += f"{self.date_done or self.scheduled_date}"
        data += (
            f"{self.tractor_license_plate_history}{self.trailer_license_plate_history}"
            f"{self.special_authorization_history}"
        )
        for move in self.move_ids:
            data += (
                f"{move.product_id.id}{move.quantity}{move.product_uom.id}{move.weight}"
            )
        return hashlib.md5(data.encode("utf-8")).hexdigest()

    def write(self, vals):
        tracked_fields = [
            ("tractor_license_plate", "tractor_license_plate_history"),
            ("trailer_license_plate", "trailer_license_plate_history"),
            ("special_authorization", "special_authorization_history"),
        ]

        history_updates = {}
        for rec in self:
            if rec.state == "done":
                for field_name, history_field in tracked_fields:
                    if field_name in vals:
                        old_val = rec[field_name]
                        new_val = vals[field_name]
                        if old_val and old_val != new_val:
                            current_history = rec[history_field] or ""
                            history_updates.setdefault(rec.id, {})[history_field] = (
                                f"{current_history}{old_val}\n"
                            )

        res = super().write(vals)

        for rec in self:
            if rec.id in history_updates:
                super(StockPicking, rec).write(history_updates[rec.id])

        return res

    def _get_share_url(self):
        self.ensure_one()
        self.check_access("read")
        if not self.deca_access_token:
            self.sudo().deca_access_token = self.env[
                "ir.attachment"
            ]._generate_access_token()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}/my/picking/{self.id}?access_token={self.deca_access_token}"

    def action_get_share_url(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": self._get_share_url(),
            "target": "new",
        }
