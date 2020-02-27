# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# (c) 2017 Diagram Software S.L.
# Copyright (c) 2017-TODAY MINORISA <ramon.guiu@minorisa.net>
# (c) 2017 Consultoría Informática Studio 73 S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Suministro Inmediato de Información en el IVA",
    "version": "8.0.1.1.0",
    "category": "Accounting & Finance",
    "website": "https://odoo-community.org/",
    "author": "Acysos S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": ["zeep",
                   "requests"],
    },
    "depends": [
        "l10n_es_aeat"
    ],
    "data": [
        "data/ir_config_parameter.xml",
        "views/res_company_view.xml",
        "views/account_invoice_view.xml",
        "views/aeat_sii_view.xml",
        "wizard/aeat_sii_password_view.xml",
        "views/aeat_sii_mapping_registration_keys_view.xml",
        "data/aeat_sii_mapping_registration_keys_data.xml",
        "views/aeat_sii_map_view.xml",
        "data/aeat_sii_map_data.xml",
        "security/ir.model.access.csv",
        "security/aeat_sii.xml"
    ],
}
