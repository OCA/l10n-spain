from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def copy(self, default=None):
        default = dict(default or {})
        if self.is_sigaus:
            default.setdefault("is_sigaus", True)
        if getattr(self, "purchase_line_id", False):
            default.setdefault("purchase_line_id", self.purchase_line_id.id)
        if getattr(self, "purchase_order_id", False):
            default.setdefault("purchase_order_id", self.purchase_order_id.id)
        return super().copy(default)
