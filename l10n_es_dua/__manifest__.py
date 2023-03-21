# Copyright 2017 Tecnativa - Antonio Espinosa
# Copyright 2019 Tecnativa - Pedro M. Baeza
# Copyright 2019 Sygel Technology - Harald Panten
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html
# See README.rst file on addon root folder for more details

{
    "name": "Importaciones con DUA",
    "category": "Localization/Account Charts",
    "version": "16.0.1.0.0",
    "development_status": "Mature",
    "depends": ["l10n_es"],
    "data": [
        "data/tax_group_data.xml",
        "data/taxes_dua.xml",
        "data/fiscal_positions_dua.xml",
        "data/fiscal_position_taxes_dua.xml",
        "data/products_dua.xml",
    ],
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "installable": True,
}
