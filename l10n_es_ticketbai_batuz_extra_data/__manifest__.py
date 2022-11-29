# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "TicketBAI - Batuz - Extra data",
    "version": "12.0.1.0.1",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Kernet Internet y Nuevas Tecnologias S.L.,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False,
    "maintainers": [
        "xAdrianC-Kernet",
        "ao-landoo",
    ],
    "depends": [
        "l10n_es_extra_data",
        "l10n_es_ticketbai_batuz"
    ],
    "data": [
        "data/tbai_tax_map_data.xml"
    ]
}
