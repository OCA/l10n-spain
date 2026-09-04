# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    pos_sequence_by_device = fields.Boolean(
        related="session_id.config_id.pos_sequence_by_device"
    )
    pos_device_id = fields.Many2one(
        "pos.device", string="POS Physical Device", readonly=True
    )

    @api.model
    def _update_sequence_number(self, pos):
        if not pos.pos_sequence_by_device:
            return super()._update_sequence_number(pos)
        return

    @api.model
    def _process_order(self, pos_order, existing_order):
        pos_order_obj = self.env["pos.order"]
        pos = self.env["pos.session"].browse(pos_order.get("session_id")).config_id
        if pos_order_obj._simplified_limit_check(
            pos_order.get("amount_total", 0), pos.l10n_es_simplified_invoice_limit
        ):
            if pos.pos_sequence_by_device and pos_order.get("pos_device_id", False):
                device = self.env["pos.device"].browse(pos_order["pos_device_id"])
                draft = pos_order.get("state") == "draft"
                if not draft:
                    device.sequence.next_by_id()
        return super()._process_order(pos_order, existing_order)

    def write(self, vals):
        for order in self.filtered(lambda o: o.config_id.pos_sequence_by_device):
            if (
                vals.get("state")
                and vals["state"] == "paid"
                and order.name == "/"
                and order.l10n_es_unique_id
            ):
                order.name = order.l10n_es_unique_id
        return super().write(vals)
