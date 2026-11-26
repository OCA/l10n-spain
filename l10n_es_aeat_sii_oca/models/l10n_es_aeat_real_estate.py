# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

# The SII joins the Basque Country and Navarre of the model 180
SITUATION_180_TO_SII = {"1": "1", "2": "2", "3": "2", "4": "3"}


class L10nEsAeatRealEstate(models.Model):
    _inherit = "l10n.es.aeat.real_estate"

    def _get_sii_situation(self):
        """Situation of the real estate in the list L6 of the SII, which joins
        the Basque Country and Navarre and adds the real estates abroad, taken
        from the situation of the model 180 so a manual one is kept."""
        self.ensure_one()
        if not self._is_in_spain():
            return "4"
        return SITUATION_180_TO_SII.get(self.real_estate_situation, "3")
