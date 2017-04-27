# -*- coding: utf-8 -*-
# Copyright 2017 Joaquin Gutierrez Pedrosa <joaquin@gutierrezweb.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Account Hierarchy Report",
    'version': "10.0.0.8.0",
    'summary': "Account Hierarchy Report",
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
    ],
    'data': [
        "security/ir.model.access.csv",
        "data/account.hierarchy.label.csv",
        "views/account_hierarchy_label.xml",
        "views/account_views.xml",
        "reports/bi_reporting_account_hierarchy.xml",
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
