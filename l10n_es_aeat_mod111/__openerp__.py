# -*- encoding: utf-8 -*-
##############################################################################
#                                                                            #
#  OpenERP, Open Source Management Solution.                                 #
#                                                                            #
#  This program is free software: you can redistribute it and/or modify      #
#  it under the terms of the GNU Affero General Public License as            #
#  published by the Free Software Foundation, either version 3 of the        #
#  License, or (at your option) any later version.                           #
#                                                                            #
#  This program is distributed in the hope that it will be useful,           #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the              #
#  GNU Affero General Public License for more details.                       #
#                                                                            #
#  You should have received a copy of the GNU Affero General Public License  #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.      #
#                                                                            #
##############################################################################

{
    'name': 'AEAT modelo 111',
    'version': '1.0',
    'category': 'Localización/Contabilidad',
    'description': """Modelo 111 de la AEAT.""",
    'author': 'OdooMRP team',
    'website': 'www.odoomrp.com',
    'license': 'AGPL-3',
    'contributors': [
        'Carlos Sánchez Cifuentes <csanchez@grupovermon.com>',
        'Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>',
    ],
    'depends': ['l10n_es_aeat'],
    'data': [
        'wizard/export_mod111_to_boe.xml',
        'views/mod111_view.xml',
        'security/ir.model.access.csv'],
    'active': False,
    'installable': True,
}
