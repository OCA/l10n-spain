# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import SQL

# Provinces of the Basque Country and Navarre (SII list L6, situation 2)
SII_FORAL_STATE_CODES = ("BI", "NA", "SS", "VI")


class L10nEsAeatRealEstate(models.Model):
    _inherit = "l10n.es.aeat.real_estate"

    owned_by_company = fields.Boolean(
        compute="_compute_owned_by_company",
        search="_search_owned_by_company",
        help="The real estate belongs to a company of this database, so it can "
        "be leased to the partner of an invoice.",
    )

    @api.depends("partner_id", "company_id.partner_id")
    def _compute_owned_by_company(self):
        for estate in self:
            estate.owned_by_company = estate.partner_id == estate.company_id.partner_id

    def _search_owned_by_company(self, operator, value):
        if operator not in ("=", "!="):
            return NotImplemented
        positive = (operator == "=") == bool(value)
        company_partners = (
            self.env["res.company"].sudo()._search([]).subselect(SQL("partner_id"))
        )
        return [("partner_id", "in" if positive else "not in", company_partners)]

    def _get_sii_property_location(self):
        """Situation of the real estate in the SII list L6, which is not the
        one of `real_estate_situation` (model 180)."""
        self.ensure_one()
        if self.country_id and self.country_id.code != "ES":
            return "4"
        if not self.reference:
            return "3"
        if self.state_id.code in SII_FORAL_STATE_CODES:
            return "2"
        return "1"

    def _get_sii_property_detail(self):
        """`DetalleInmueble` of the SII for this real estate."""
        self.ensure_one()
        detail = {"SituacionInmueble": self._get_sii_property_location()}
        if self.reference:
            detail["ReferenciaCatastral"] = self._normalize_reference(self.reference)
        return detail
