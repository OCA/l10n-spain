# -*- coding: utf-8 -*-
# Copyright 2013-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class BetterZipGeonamesImport(models.TransientModel):
    _inherit = 'better.zip.geonames.import'

    @api.model
    def transform_city_name(self, city, country):
        """Change determinants casing."""
        if country.code == 'ES':
            return city.replace(' De ', ' de ').replace(' Del ', ' del ').\
                replace(' La ', ' la ').replace(' Las ', ' las ').\
                replace(' El ', ' el ').replace(' Los ', ' los ')
        else:
            return super(BetterZipGeonamesImport, self).transform_city_name(
                city, country)

    @api.model
    def select_or_create_state(self, row, country, code_row_index=4,
                               name_row_index=3):
        if country.code == 'ES':
            code_row_index = 6
            name_row_index = 5
        return super(BetterZipGeonamesImport, self).select_or_create_state(
            row, country, code_row_index=code_row_index,
            name_row_index=name_row_index)
