# Copyright 2018 Studio73 - Abraham Anes
# Copyright 2019 Studio73 - Pablo Fuentes
# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sistema de comprobación y contraste de facturas enviadas al SII",
    "version": "16.0.2.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Studio73, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "external_dependencies": {"python": ["deepdiff<8", "zeep"]},
    "depends": ["l10n_es_aeat_sii_oca"],
    "data": [
        "security/ir.model.access.csv",
        "security/aeat_sii.xml",
        "data/queue_job.xml",
        "views/account_move_views.xml",
        "views/aeat_sii_match_report.xml",
    ],
    "installable": True,
    "maintainers": ["Abranes", "Reyes4711-S73"],
}
