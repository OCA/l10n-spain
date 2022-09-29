# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class CTTExpressPickupWizard(models.TransientModel):
    _name = "cttexpress.pickup.wizard"
    _description = "Generate shipping pickups"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        domain=[("delivery_type", "=", "cttexpress")],
    )
    delivery_date = fields.Date(
        required=True, default=fields.Date.context_today
    )
    min_hour = fields.Float(required=True)
    max_hour = fields.Float(required=True, default=23.99)
    code = fields.Char(readonly=True)
    state = fields.Selection(
        selection=[("new", "new"), ("done", "done")],
        default="new",
        readonly=True,
    )

    @api.onchange('min_hour', 'max_hour')
    def _onchange_hours(self):
        """Min and max hours UX"""
        # Avoid negative or after midnight
        self.min_hour = min(self.min_hour, 23.99)
        self.min_hour = max(self.min_hour, 0.0)
        self.max_hour = min(self.max_hour, 23.99)
        self.max_hour = max(self.max_hour, 0.0)
        # Avoid wrong order
        self.max_hour = max(self.max_hour, self.min_hour)

    def create_pickup_request(self):
        """Get the pickup code"""
        def convert_float_time_to_str(float_time):
            """Helper to pass the times in the expexted format 'HH:MM'"""
            return "{0:02.0f}:{1:02.0f}".format(*divmod(float_time * 60, 60))

        ctt_request = self.carrier_id._ctt_request()
        delivery_date = fields.Date.to_string(self.delivery_date)
        error, code = ctt_request.create_request(
            delivery_date,
            convert_float_time_to_str(self.min_hour),
            convert_float_time_to_str(self.max_hour)
        )
        self.carrier_id._ctt_check_error(error)
        self.carrier_id._ctt_log_request(ctt_request)
        self.code = code
        self.state = "done"
        return dict(
            self.env["ir.actions.act_window"].for_xml_id(
                "delivery_cttexpress",
                "action_delivery_cttexpress_pickup_wizard"
            ),
            res_id=self.id
        )
