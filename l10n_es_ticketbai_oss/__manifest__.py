# Copyright 2022 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "TicketBAI - OSS",
    "version": "15.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Landoo Sistemas de Información S.L, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False,
    "development_status": "Beta",
    "maintainers": ["ao-landoo"],
    "depends": [
        "l10n_es_ticketbai",
        "l10n_eu_oss_oca",
    ],
    "data": [
        "data/vat_regime_key_data.xml",
    ],
}
