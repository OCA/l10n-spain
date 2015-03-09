# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011-2013 Acysos S.L. (http://acysos.com)
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
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
    'name': 'Generación de fichero modelo 340. Registro tipo 0',
    'version': '1.0',
    'author': "Acysos S.L.,Odoo Community Association (OCA)",
    'website': 'www.acysos.com',
    'category': 'Localisation/Accounting',
    'description': '''
        Exporta el registro de tipo 0 del Modelo 340.
        Actualmente solo obligatorio para la Comunidad Foral de Navarra.
        ''',
    'license': 'AGPL-3',
    'depends': [
        'l10n_es_aeat_mod340',
        'base_location',
    ],
    'data': [
        'mod340_view.xml'
    ],
    'installable': True,
}
