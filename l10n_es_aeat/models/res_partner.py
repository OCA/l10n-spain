# Copyright 2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from odoo.tools import ormcache


class ResPartner(models.Model):
    _inherit = "res.partner"

    aeat_anonymous_cash_customer = fields.Boolean(
        string="AEAT - Anonymous customer",
        help="Check this for anonymous cash customer. AEAT communication",
    )

    def _map_aeat_country_code(self, country_code):
        country_code_map = {"RE": "FR", "GP": "FR", "MQ": "FR", "GF": "FR", "EL": "GR"}
        return country_code_map.get(country_code, country_code)

    @ormcache("self.env")
    def _get_aeat_europe_codes(self):
        europe = self.env.ref("base.europe", raise_if_not_found=False)
        if not europe:
            europe = self.env["res.country.group"].search(
                [("name", "=", "Europe")], limit=1
            )
        return europe.country_ids.mapped("code")

    @ormcache("self.vat, self.country_id")
    def _parse_aeat_vat_info(self):
        """Return tuple with split info (country_code, identifier_type and
        vat_number) from vat and country partner
        """
        self.ensure_one()
        vat_number = self.vat or ""
        prefix = self._map_aeat_country_code(vat_number[:2].upper())
        if prefix in self._get_aeat_europe_codes():
            country_code = prefix
            vat_number = vat_number[2:]
            identifier_type = "02"
        else:
            country_code = self._map_aeat_country_code(self.country_id.code) or ""
            if country_code in self._get_aeat_europe_codes():
                identifier_type = "02"
            else:
                identifier_type = "04"
        if country_code == "ES":
            identifier_type = ""
        return country_code, identifier_type, vat_number
