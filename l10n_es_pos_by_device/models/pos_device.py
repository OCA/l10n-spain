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
        readonly=True,
        compute="_compute_simplified_invoice_sequence",
    )
    device_simplified_invoice_padding = fields.Integer(
        "Simplified Invoice padding",
        readonly=True,
        compute="_compute_simplified_invoice_sequence",
    )
    device_simplified_invoice_number = fields.Integer(
        "Sim.Inv number",
        readonly=True,
        compute="_compute_simplified_invoice_sequence",
    )

    def lock_device(self):
        return self.write({"locked": True})

    def unlock_device(self):
        return self.write({"locked": False})

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
