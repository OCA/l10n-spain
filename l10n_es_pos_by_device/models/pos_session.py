from odoo import models
from odoo.osv import expression


class PosSession(models.Model):
    _inherit = "pos.session"

    def open_frontend_cb(self):
        for session in self:
            if session.config_id.pos_sequence_by_device:
                session.config_id._check_available_devices()
        return super(PosSession, self).open_frontend_cb()

    def _loader_params_pos_device(self):
        config = self.config_id
        domain = [("company_id", "=", config.company_id.id), ("locked", "=", False)]
        if config.pos_device_ids:
            domain = expression.AND([domain, [("id", "in", config.pos_device_ids.ids)]])
        return {
            "search_params": {
                "domain": domain,
                "fields": [
                    "name",
                    "sequence",
                    "locked",
                    "company_id",
                    "device_simplified_invoice_prefix",
                    "device_simplified_invoice_padding",
                    "device_simplified_invoice_number",
                ],
            },
        }

    def _pos_ui_models_to_load(self):
        return super()._pos_ui_models_to_load() + ["pos.device"]

    def _get_pos_ui_pos_device(self, params):
        return self.env["pos.device"].search_read(**params["search_params"])
