# Copyright 2022 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "TicketBAI - Batuz con DUA",
    "version": "12.0.1.0.1",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Landoo Sistemas de Información S.L, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "maintainers": [
        "ao-landoo",
    ],
    "depends": [
        "l10n_es_ticketbai_batuz",
        "l10n_es_dua",
    ],
    "data": [
        "data/account_fiscal_position_template_data.xml",
        "data/tax_code_map_dua_ticketbai_data.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": True,
}
