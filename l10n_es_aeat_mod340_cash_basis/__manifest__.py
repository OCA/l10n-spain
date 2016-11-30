# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2016 Factor Libre S.L. (http://factorlibre.com)
#                       Kiko Peiro <francisco.peiro@factorlibre.com>
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Extensión del modelo 340 para criterio de caja',
    'version': '8.0.1.0.0',
    'author': "Odoo Community Association (OCA), "
              "Factor Libre, "
              "GAFIC SLP - Albert Cabedo",
    'website': 'https://github.com/OCA/l10n-spain',
    'category': 'Localisation/Accounting',
    'license': 'AGPL-3',
    'depends': [
        'l10n_es_aeat_mod340',
        'account_vat_on_payment'
    ],
    'data': [
    ],
    'installable': False,
}
