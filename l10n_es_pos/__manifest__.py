# -*- coding: utf-8 -*-
# See README.rst file on addon root folder for license details

{
    'name': "Punto de venta adaptado a la legislación española",
    'summary': """
        Añade todo lo necesario para adaptar el TPV a la legislación Española.
    """,
    'description': """
Añade todo lo necesario para adaptar el TPV a la legislación Española.
    """,

    'website': "https://www.aselcis.com",
    'category': 'Point Of Sale',
    'author': "Antiun Ingeniería S.L., "
              "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "Aselcis Consulting, "
              "Spanish Localization Team, "
              "Odoo Community Association (OCA)",
    'version': '10.0.1.0.0',
    'depends': ['point_of_sale'],
    'license': 'AGPL-3',
    'data': [
        'views/pos_templates.xml',
        'views/pos_views.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
}
