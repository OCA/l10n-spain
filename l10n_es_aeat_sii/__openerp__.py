# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Alberto Martín Cortada <alberto.martin@guadaltech.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Suministro Inmediato de Información en el IVA",
    "version": "6.1.0.1",
    "category": "Accounting & Finance",
    "website": "https://odoo-community.org/",
    "author": "Acysos S.L., "
              "Alberto Martín Cortada - Guadaltehch, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": ["zeep",
                   "requests"],
    },
    "depends": [
        "account_refund_original",
        "l10n_es_aeat",

    ],
    "data": [
        "data/ir_config_parameter.xml",
        "views/res_company_view.xml",
        "views/account_invoice_view.xml",
        "views/aeat_sii_view.xml",
        "views/aeat_sii_map_view.xml",
        "views/aeat_sii_mapping_registration_keys_view.xml",
        "wizard/aeat_sii_password_view.xml",
        "views/aeat_sii_mapping_registration_keys_view.xml",
        "data/aeat_sii_mapping_registration_keys_data.xml",
        "views/aeat_sii_map_view.xml",
        "data/aeat_sii_map_data.xml",
        "security/ir.model.access.csv",
        "security/aeat_sii.xml"
    ],
}
