# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Suministro Inmediato de Información en el IVA",
    "version": "8.0.1.0.1",
    "category": "Accounting & Finance",
    "website": "https://odoo-community.org/",
    "author": "Acysos S.L., Alberto Martín Cortada - Guadaltehch, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": ["zeep",
                   "requests"],
    },
    "depends": [
        "base",
        "account"
    ],
    "data": [
        "data/ir_config_parameter.xml",
        "views/res_company_view.xml",
        "views/account_invoice_view.xml"
    ],
}
