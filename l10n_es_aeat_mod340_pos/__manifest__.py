# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Miguel Paraiso - Aselcis Consulting (http://www.aselcis.com). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
{
    'name': 'Generación de fichero modelo 340 y libro de IVA para el TPV',
    'summary': 'Añade compatibilidad con el TPV al modelo 340',
    'version': '10.0.1.0.0',
    'depends': ['l10n_es_aeat_mod340', 'point_of_sale', 'l10n_es_pos',
                'l10n_es_partner'],
    'category': 'Localisation/Accounting',
    'author': 'Aselcis Consulting, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-spain',
    'description': """
Añade compatibilidad con el TPV al modelo 340.

IMPORTANTE:
1. Los datos del modelo 340 serán correctos en los nuevos pedidos del TPV que
se generen una vez instalado este módulo.
2. Es necesario desactivar la opción de 'Agrupar apuntes' de la configuración
de cada TPV, esta operación se realizará automáticamente al instalar este
módulo.
    """,
    'license': 'AGPL-3',
    'data': [
        'data/mod340_pos.xml',
        'views/mod340_view.xml',
    ],
    'installable': True,

}
