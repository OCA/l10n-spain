# Copyright 2013-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class BetterZipGeonamesImport(models.TransientModel):
    _inherit = "city.zip.geonames.import"

    @api.model
    def transform_city_name(self, city, country):
        """Change determinants casing."""
        res = super().transform_city_name(city, country)
        if country.code == "ES":
            res = (
                res.replace(" De ", " de ")
                .replace(" Del ", " del ")
                .replace(" La ", " la ")
                .replace(" Las ", " las ")
                .replace(" El ", " el ")
                .replace(" Los ", " los ")
            )
        return res
