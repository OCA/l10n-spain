# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    def reverse_moves(self, is_modify=False):
        res = super().reverse_moves(is_modify=is_modify)
        self.move_ids.filtered(lambda mov: mov.move_type == "out_invoice").mapped(
            "reversal_move_ids"
        ).write({"verifactu_refund_type": "I"})
        return res
