##############################################################################
#
# Copyright (c) 2023 Binhex System Solutions
# Copyright (c) 2023 Nicolás Ramos (http://binhex.es)
#
# The licence is in the file __manifest__.py
##############################################################################

{
    "name": "ATC Menú",
    "summary": "Modulo base para menú de la ATC",
    "version": "16.0.1.0.0",
    "author": "Binhex System Solutions",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Accounting & Finance",
    "depends": ["l10n_es_igic"],
    "data": [
        "security/atc_security.xml",
        "views/atc_menuitem.xml",
        "data/atc_partner.xml",
    ],
    "installable": True,
    "maintainers": ["nicolasramos"],
}
