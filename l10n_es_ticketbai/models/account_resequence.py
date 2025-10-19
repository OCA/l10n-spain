#  Copyright 2021 Landoo Sistemas de Informacion SL
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, exceptions, models


class ReSequenceWizard(models.TransientModel):
    _inherit = "account.resequence.wizard"

    def resequence(self):
        if (
            len(
                self.move_ids.filtered(
                    lambda m: m.move_type in {"out_invoice", "out_refund"}
                    and m.company_id.tbai_enabled
                )
            )
            > 0
        ):
            raise exceptions.UserError(
                _(
                    "You cannot resequence a customer "
                    "invoice when TicketBAI is enabled."
                )
            )
        return super(ReSequenceWizard, self).resequence()
