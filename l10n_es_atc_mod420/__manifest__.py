# Copyright 2014-2022 Nicolás Ramos (http://binhex.cloud)
# Copyright 2023-2024 Christian Ramos (http://binhex.cloud)
# Copyright 2023 Binhex System Solutions

{
    "name": "ATC Modelo 420",
    "version": "16.0.1.1.0",
    "author": "Binhex, Odoo Community Association (OCA)",
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_aeat", "l10n_es_igic", "l10n_es_atc"],
    "data": [
        "data/tax_code_map_mod420_data.xml",
        "views/mod420_view.xml",
        "security/ir.model.access.csv",
    ],
    "maintainers": ["Christian-RB"],
    "installable": True,
    "auto_install": False,
}
