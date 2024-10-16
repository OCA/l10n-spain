# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    def reverse_moves(self):
        if any(move.is_sigaus for move in self.move_ids):
            self = self.with_context(reverse_has_sigaus=True)
        return super().reverse_moves()
