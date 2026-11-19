# Copyright 2026 Binhex
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    l10n_es_exempt_reason = fields.Selection(
        selection="_get_l10n_es_exempt_reasons",
    )

    @api.model
    def _get_l10n_es_exempt_reasons(self):
        reasons = [
            ("E1", "Art. 20"),
            ("E2", "Art. 21"),
            ("E3", "Art. 22"),
            ("E4", "Art. 23 y 24"),
            ("E5", "Art. 25"),
            ("E6", "Otros"),
        ]
        agency = self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias", raise_if_not_found=False
        )
        if agency and self.env.company.tax_agency_id == agency:
            reasons.extend(
                [
                    ("E7", "Art. 110 Ley 4/2012"),
                    ("E8", "Otros (IGIC)"),
                ]
            )
        return reasons
