# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from odoo import models


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.mod303.report"

    def get_taxes_from_map(self, map_line):
        if map_line.field_number == 44 and self.company_id.with_vat_prorate:
            return self.env["account.tax"].search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("with_vat_prorate", "=", True),
                ]
            )
        return super().get_taxes_from_map(map_line)

    def _get_move_line_domain(self, date_start, date_end, map_line):
        """Se define el importe de la prorata para la casilla 44.
        Ejemplo: 10€ y prorata del 99%, se devolverá 9.9
        """
        res = super()._get_move_line_domain(date_start, date_end, map_line)
        if map_line.field_number == 44 and self.company_id.with_vat_prorate:
            res += [("vat_prorate", "=", False)]
        return res
