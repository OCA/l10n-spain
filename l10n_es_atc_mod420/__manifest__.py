# Copyright 2014-2022 Nicolás Ramos (http://binhex.es)
# Copyright 2023 Binhex System Solutions

{
    "name": "ATC Modelo 420",
    "version": "16.0.4.0.0",
    "author": "Binhex System Solutions," 
    "Odoo Community Association (OCA)",
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_aeat", "l10n_es_igic", "l10n_es_atc"],
    "data": [
        "data/tax_code_map_mod420_data.xml",
        "views/mod420_view.xml",
        "security/ir.model.access.csv",
    ],
    "maintainers": ["nicolasramos"],
    "installable": True,
    "auto_install": False,
    # "pre_init_hook": "pre_init_check", Queda pendiente hasta saber que versión de l10n_es_igic se va a usar por diferencias de impuestos
}
