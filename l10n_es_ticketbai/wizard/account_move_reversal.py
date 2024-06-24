# Copyright 2020 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    def reverse_moves(self):
        if self.refund_method == "modify":
            move_id = (
                self.env["account.move"].browse(self.env.context["active_ids"])
                if self.env.context.get("active_model") == "account.move"
                else self.move_id
            )
            move_id.tbai_substitution_invoice_id = move_id.id
        return super(
            AccountMoveReversal, self.with_context(refund_method=self.refund_method)
        ).reverse_moves()

    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        res.update({"company_id": self.move_ids[0].company_id.id})
        return res
