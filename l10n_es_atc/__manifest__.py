# Copyright 2023 Binhex - Nicolás Ramos (http://binhex.es)

{
    "name": "ATC Base",
    "summary": "Módulo base para declaraciones de la ATC",
    "version": "20.0.1.0.0",
    "author": "Binhex, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Accounting",
    "depends": ["l10n_es_aeat"],
    "data": [
        "security/aeat_security.xml",
        "data/config_parameter_data.xml",
        "views/atc_menuitem.xml",
        "data/atc_partner.xml",
        "views/res_company_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
