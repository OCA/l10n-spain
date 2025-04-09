# Copyright 2025 APSL-Nagarro Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class L10nEsVatBook(models.Model):
    _inherit = "l10n.es.vat.book"

    def _check_exceptions(self, line_vals):
        res = super()._check_exceptions(line_vals)
        pos_session = self.env["pos.session"].search(
            [("move_id", "=", line_vals["move_id"])]
        )
        if pos_session and not line_vals["partner_id"]:
            line_vals.pop("exception_text")
        return res
