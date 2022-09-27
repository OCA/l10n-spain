# Copyright 2016 Comunitea - Omar Castiñeira
# Copyright 2013-2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Statement Avoid Duplicated Line",
    "author": "Domatix," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "version": "14.0.1.0.1",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["l10n_es_account_statement_import_n43"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_bank_statement_views.xml",
        "wizard/duplicated_n43_wizard_views.xml",
    ],
}
