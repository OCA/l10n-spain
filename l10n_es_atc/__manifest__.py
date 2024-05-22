# Copyright 2023 Binhex - Nicolás Ramos (http://binhex.es)

{
    "name": "ATC Menú",
    "summary": "Modulo 'glue' de la AEAT para el menú de la ATC",
    "version": "16.0.1.0.1",
    "author": "Binhex System Solutions," "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Accounting",
    "depends": ["l10n_es_aeat"],
    "data": [
        "security/atc_security.xml",
        "views/atc_menuitem.xml",
        "data/atc_partner.xml",
    ],
    "installable": True,
    "auto_install": True,
}
