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
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        if ui_order.get("pos_device", False):
            res.update({"pos_device_id": ui_order["pos_device"]})
        return res

    @api.model
    def _update_sequence_number(self, pos):
        if not pos.pos_sequence_by_device:
            return super(PosOrder, self)._update_sequence_number(pos)
        return

    @api.model
    def _process_order(self, pos_order, draft, existing_order):
        order_data = pos_order.get("data", {})
        pos_order_obj = self.env["pos.order"]
        pos = self.env["pos.session"].browse(order_data.get("pos_session_id")).config_id
        if pos_order_obj._simplified_limit_check(
            order_data.get("amount_total", 0), pos.l10n_es_simplified_invoice_limit
        ):
            if pos.pos_sequence_by_device and order_data.get("device", False):
                device_seq = self.env["ir.sequence"].browse(
                    order_data["device"]["sequence"][0]
                )
                if not draft:
                    device_seq.next_by_id()
                pos_order["data"].update({"pos_device": order_data["device"]["id"]})
        return super(PosOrder, self)._process_order(pos_order, draft, existing_order)

    def write(self, vals):
        for order in self.filtered(lambda o: o.config_id.pos_sequence_by_device):
            if (
                vals.get("state")
                and vals["state"] == "paid"
                and order.name == "/"
                and order.l10n_es_unique_id
            ):
                order.name = order.l10n_es_unique_id
        return super(PosOrder, self).write(vals)
