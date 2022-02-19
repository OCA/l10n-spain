# Copyright 2022 Bilbonet - Jesus Ramiro
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# See README.rst file on addon root folder for more details
{
    "name": "REAV - Régimen Especial Agencias de Viajes",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "Localization/Account Charts",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Bilbonet, Odoo Community Association (OCA)",
    "maintainers": ["Bilbonet"],
    "license": "AGPL-3",
    "depends": ["l10n_es"],
    "data": [
        "data/tax_group_data.xml",
        "data/taxes_reav.xml",
        "data/fiscal_positions_reav.xml",
        "data/fiscal_position_taxes_reav.xml",
    ],
}
