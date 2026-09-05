from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def copy(self, default=None):
        # 18.0: copy now works on multi-recordsets; keep per-record defaults
        copied = self.env["account.move.line"]
        for rec in self:
            rec_default = dict(default or {})
            if rec.is_sigaus:
                rec_default.setdefault("is_sigaus", True)
            if getattr(rec, "purchase_line_id", False):
                rec_default.setdefault("purchase_line_id", rec.purchase_line_id.id)
            if getattr(rec, "purchase_order_id", False):
                rec_default.setdefault("purchase_order_id", rec.purchase_order_id.id)
            copied |= super(AccountMoveLine, rec).copy(rec_default)
        return copied
