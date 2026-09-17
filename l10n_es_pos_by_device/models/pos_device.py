# Copyright 2023 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PosDevice(models.Model):
    _name = "pos.device"
    _description = "PoS Device"

    name = fields.Char(required=True)
    sequence = fields.Many2one("ir.sequence", required=True)
    locked = fields.Boolean(readonly=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    device_simplified_invoice_prefix = fields.Char(
        "Simplified Invoice prefix",
        compute="_compute_simplified_invoice_sequence",
    )
    device_simplified_invoice_padding = fields.Integer(
        "Simplified Invoice padding",
        compute="_compute_simplified_invoice_sequence",
    )
    device_simplified_invoice_number = fields.Integer(
        "Sim.Inv number",
        compute="_compute_simplified_invoice_sequence",
    )

    def lock_device(self):
        self.locked = True
        return True

    def unlock_device(self):
        self.locked = False
        return True

    @api.depends(
        "sequence.number_next_actual",
        "sequence.prefix",
        "sequence.padding",
    )
    def _compute_simplified_invoice_sequence(self):
        for dev in self:
            seq = dev.sequence
            dev.device_simplified_invoice_number = (
                seq._get_current_sequence().number_next_actual
            )
            dev.device_simplified_invoice_prefix = seq._get_prefix_suffix()[0]
            dev.device_simplified_invoice_padding = seq.padding

    def _load_pos_data_domain(self, data):
        config_id = data["pos.config"]["data"][0]["id"]
        config = self.env["pos.config"].browse(config_id)
        domain = [("company_id", "=", config.company_id.id), ("locked", "=", False)]
        if config.pos_device_ids:
            domain += [("id", "in", config.pos_device_ids.ids)]
        return domain

    @api.model
    def _load_pos_data_fields(self, config_id):
        return [
            "name",
            "sequence",
            "locked",
            "company_id",
            "device_simplified_invoice_prefix",
            "device_simplified_invoice_padding",
            "device_simplified_invoice_number",
        ]

    def _load_pos_data(self, data):
        domain = self._load_pos_data_domain(data)
        fields = self._load_pos_data_fields(data["pos.config"]["data"][0]["id"])
        return {
            "data": self.search_read(domain, fields, load=False),
            "fields": fields,
        }
