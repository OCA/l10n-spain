# -*- coding: utf-8 -*-
# © 2017 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Envío de Factura-e a FACe",
    "version": "10.0.1.0.0",
    "author": "Creu Blanca, "
              "Odoo Community Association (OCA)",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "l10n_es_facturae",
    ],
    "data": [
        "data/face_data.xml",
        "views/res_company_view.xml",
        "views/res_config_views.xml",
        "wizard/account_invoice_integration_cancel_view.xml"
    ],
    "external_dependencies": {
        "python": [
            "OpenSSL",
            "zeep",
            "xmlsec"
        ]
    },
    "installable": True,
}
