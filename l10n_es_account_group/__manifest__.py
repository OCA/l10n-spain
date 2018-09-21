# coding: utf-8
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Spanish Account Groups",
    "summary": "Account groups for Spanish chart of accounts",
    "version": "10.0.1.0.0",
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Tecnativa,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "l10n_es",
        "account_group",
    ],
    "data": [
        "data/account_group_data.xml",
        "data/account_account_template_common_data.xml",
        "data/account_account_template_assoc_data.xml",
        "data/account_account_template_full_data.xml",
        "data/account_account_template_pymes_data.xml",
    ],
}
