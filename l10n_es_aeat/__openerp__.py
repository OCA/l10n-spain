# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es)
#        Luis Manuel Angueira Blanco
#    Copyright (C) 2013
#        Ignacio Ibeas - Acysos S.L. (http://acysos.com)
#        Migración a OpenERP 7.0
#    Copyright (C) 2013-2015
#        Serv. Tecnol. Avanzados - Pedro M. Baeza (www.serviciosbaeza.com)
#    Copyright (C) 2015
#        Ainara Galdona - AvanzOSC (https://www.avanzosc.es)
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
    'author': "Pexego,"
              "Serv. Tecnol. Avanzados - Pedro M. Baeza,"
              "AvanzOSC,"
              "Odoo Community Association (OCA)",
    'license': "AGPL-3",
    'contributors': [
        'Ignacio Ibeas (Acysos S.L.)',
        'Ainara Galdona',
        'Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>',
    ],
    'website': "https://github.com/OCA/l10n-spain",
    'category': "Accounting & Finance",
    'depends': [
        "account",
    ],
    'external_dependencies': {
        'python': ['unidecode'],
    },
    'data': [
        'security/aeat_security.xml',
        'security/ir.model.access.csv',
        'data/aeat_sequence_type.xml',
        'wizard/export_to_boe_wizard.xml',
        'views/aeat_menuitem.xml',
        'views/aeat_view.xml',
        'views/aeat_export_configuration_view.xml',
        'views/aeat_tax_code_mapping_view.xml'
    ],
    'installable': True,
}
