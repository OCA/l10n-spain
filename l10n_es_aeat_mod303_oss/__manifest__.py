# Copyright 2021 PESOL - Angel Moya
# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

{
    "name": "AEAT modelo 303 - OSS",
    "version": "16.0.1.0.1",
    "category": "Accounting",
    "author": "PESOL, Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_aeat_mod303", "l10n_eu_oss_oca"],
    "data": [
        "data/2021-07/l10n_es_aeat_map_tax_line.xml",
        "data/2023/l10n_es_aeat_map_tax_line.xml",
    ],
    "installable": True,
    "autoinstall": True,
}
