# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es)
#        Luis Manuel Angueira Blanco
#    Copyright (C) 2013
#        Ignacio Ibeas - Acysos S.L. (http://acysos.com)
#        Migración a OpenERP 7.0
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
    'name': "AEAT Base",
    'version': "1.1",
    'author': "Pexego",
    'license': "AGPL-3",
    'contributors': [
        'Ignacio Ibeas (Acysos S.L.)',
        'Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>',
    ],
    'website': "http://www.pexego.es, http://www.acysos.com",
    'category': "Localisation/Accounting",
    'depends': [
        "account",
    ],
    'external_dependencies': {
        'python': ['unidecode'],
    },
    'description': """
Módulo base para declaraciones de la AEAT.
    """,
    'data': [
        'security/aeat_security.xml',
        'security/ir.model.access.csv',
        'wizard/export_to_boe_wizard.xml',
        'aeat_menuitem.xml',
        'aeat_view.xml',
    ],
    'installable': True,
}
