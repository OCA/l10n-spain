# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

# Situation of the model 180 list in the one of the model 347
SITUATION_180_TO_347 = {"1": "1", "2": "2", "3": "2", "4": "3"}


class L10nEsAeatRealEstate(models.Model):
    _inherit = "l10n.es.aeat.real_estate"

    def _get_mod347_situation(self):
        """Situation in the list of the model 347, which joins the Basque
        Country and Navarre and adds the real estates abroad, taken from the
        situation of the model 180 so a manual one is kept."""
        self.ensure_one()
        if not self._is_in_spain():
            return "4"
        return SITUATION_180_TO_347.get(self.real_estate_situation, "3")

    def _get_mod347_location(self):
        """Locality, municipality, INE municipality code, province code and zip
        of the model 347. The locality is only given when it is not the
        municipality, and the province is the numeric code of the INE, not the
        code of the state."""
        self.ensure_one()
        municipality = self.municipality or self.city or ""
        return {
            "locality": self.city if self.city != municipality else "",
            "municipality": municipality,
            "municipality_code": self.municipality_code or "",
            "province_code": (
                (self.municipality_code or self.zip or "")[:2]
                if self._is_in_spain()
                else ""
            ),
            "zip": self.zip or "",
        }
