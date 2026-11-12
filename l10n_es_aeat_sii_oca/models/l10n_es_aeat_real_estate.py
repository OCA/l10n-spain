# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class L10nEsAeatRealEstate(models.Model):
    _inherit = "l10n.es.aeat.real_estate"

    def _get_sii_property_detail(self):
        """`DetalleInmueble` of the SII for this real estate."""
        self.ensure_one()
        detail = {"SituacionInmueble": self._get_sii_347_situation()}
        if self.reference:
            detail["ReferenciaCatastral"] = self._normalize_reference(self.reference)
        return detail
