from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _validate_session(self):
        res = super()._validate_session()
        self.order_ids.send_sii()
        return res
