# -*- coding: utf-8 -*-
# Copyright 2017 Joaquin Gutierrez Pedrosa <joaquin@gutierrezweb.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Account Groups",
    'version': "11.0.0.8.0",
    'summary': "Spanish Account Group",
    'sequence': 51,
    'category': "Accounting",
    'author': "Joaquin Gutierrez Pedrosa,"
              "Odoo Community Association (OCA)",
    'license': "AGPL-3",
    'website': "https://www.gutierrezweb.es",
    'images': [
    ],
    'depends': [
        "account",
        "l10n_es",
    ],
    'data': [
        "data/account_group_data.xml",
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
