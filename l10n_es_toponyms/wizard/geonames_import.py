# -*- coding: utf-8 -*-
# © 2013-2016 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api

STATES_REPLACE_LIST = {
    'VI': '01',
    'AB': '02',
    'A': '03',
    'AL': '04',
    'AV': '05',
    'BA': '06',
    'PM': '07',
    'B': '08',
    'BU': '09',
    'CC': '10',
    'CA': '11',
    'CS': '12',
    'CR': '13',
    'CO': '14',
    'C': '15',
    'CU': '16',
    'GI': '17',
    'GR': '18',
    'GU': '19',
    'SS': '20',
    'H': '21',
    'HU': '22',
    'J': '23',
    'LE': '24',
    'L': '25',
    'LO': '26',
    'LU': '27',
    'M': '28',
    'MA': '29',
    'MU': '30',
    'NA': '31',
    'OR': '32',
    'O': '33',
    'P': '34',
    'GC': '35',
    'PO': '36',
    'SA': '37',
    'TF': '38',
    'S': '39',
    'SG': '40',
    'SE': '41',
    'SO': '42',
    'T': '43',
    'TE': '44',
    'TO': '45',
    'V': '46',
    'VA': '47',
    'BI': '48',
    'ZA': '49',
    'Z': '50',
    'CE': '51',
    'ME': '52',
}


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
            # Replace state code
            code_row_index = 6
            name_row_index = 5
            row[code_row_index] = STATES_REPLACE_LIST[row[code_row_index]]
        return super(BetterZipGeonamesImport, self).select_or_create_state(
            row, country, code_row_index=code_row_index,
            name_row_index=name_row_index)
