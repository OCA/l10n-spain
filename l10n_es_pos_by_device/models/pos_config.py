# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = "pos.config"

    pos_sequence_by_device = fields.Boolean(related="company_id.pos_sequence_by_device")
    pos_device_ids = fields.Many2many(
        "pos.device",
        string="Available POS devices",
        help="If left empty, all devices will be selectable",
    )

    def _check_available_devices(self):
        self.ensure_one()
        if len(self.pos_device_ids) > 0:
            return
        devices = self.env["pos.device"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("locked", "=", False),
            ]
        )
        if len(devices) == 0:
            raise ValidationError(
                _("There are no physical devices available. Cannot start session.")
            )

    def open_ui(self):
        for config in self:
            if config.pos_sequence_by_device:
                config._check_available_devices()
        return super(PosConfig, self).open_ui()

    def open_session_cb(self, check_coa=True):
        for config in self:
            if config.pos_sequence_by_device:
                config._check_available_devices()
        return super(PosConfig, self).open_session_cb(check_coa)

    def _open_session(self, session_id):
        for config in self:
            if config.pos_sequence_by_device:
                config._check_available_devices()
        return super(PosConfig, self)._open_session(session_id)

    @api.depends("pos_sequence_by_device")
    def _compute_simplified_config(self):
        # pylint: disable=missing-return
        super()._compute_simplified_config()
        for config in self:
            config.is_simplified_config = (
                config.is_simplified_config or config.pos_sequence_by_device
            )
