# -*- coding: utf-8 -*-
# See README.rst file on addon root folder for license details

{
    "name": "Punto de venta adaptado a la legislación española",
    "version": "8.0.1.0.0",
    "author": "Antiun Ingeniería S.L., "
              "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "Spanish Localization Team, "
              "Odoo Community Association (OCA)",
    "website": "http://www.antiun.com",
    "license": "AGPL-3",
    "category": "Point Of Sale",
    "depends": [
        'base',
        'point_of_sale',
        'pos_pricelist'
    ],
    'data': [
        "views/pos_template.xml",
        "views/point_of_sale_view.xml",
        "views/point_of_sale_report.xml",
        "reports/common.xml",
        "reports/receipt_report.xml",
    ],
    "qweb": [
        'static/src/xml/pos.xml',
    ],
    'installable': False,
}
