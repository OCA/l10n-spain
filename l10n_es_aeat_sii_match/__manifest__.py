# Copyright 2018 Studio73 - Abraham Anes
# Copyright 2019 Studio73 - Pablo Fuentes
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sistema de comprobación y contraste de facturas enviadas al SII",
    "version": "11.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Studio73," "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "external_dependencies": {
        "python": [
            "deepdiff",
        ],
    },
    "depends": [
        "l10n_es_aeat_sii",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/aeat_sii.xml",
        "views/account_invoice_view.xml",
        "views/aeat_sii_match_report.xml",
    ],
}
