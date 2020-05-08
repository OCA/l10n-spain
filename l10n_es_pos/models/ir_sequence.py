# Copyright 2018 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    @api.constrains("prefix", "code")
    def check_simplified_invoice_unique_prefix(self):
        if self._context.get("copy_pos_config"):
            return
        for sequence in self.filtered(
            lambda x: x.code == "pos.config.simplified_invoice"
        ):
            if (
                self.search_count(
                    [
                        ("code", "=", "pos.config.simplified_invoice"),
                        ("prefix", "=", sequence.prefix),
                    ]
                )
                > 1
            ):
                raise UserError(
                    _(
                        "There is already a simplified invoice "
                        "sequence with that prefix and it should be "
                        "unique."
                    )
                )
