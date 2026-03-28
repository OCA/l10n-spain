from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def open_frontend_cb(self):
        for session in self:
            if session.config_id.pos_sequence_by_device:
                session.config_id._check_available_devices()
        return super().open_frontend_cb()

    def _load_pos_data_models(self, config_id):
        result = super()._load_pos_data_models(config_id)
        config = self.env["pos.config"].browse(config_id)
        if config.pos_sequence_by_device:
            result.append("pos.device")
        return result
