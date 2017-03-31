# -*- coding: utf-8 -*-
# Copyright 2017 Joaquin Gutierrez Pedrosa <joaquin@gutierrezweb.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Hierarchy Report',
    'version': '10.0.0.8.0',
    'summary': 'Account Hierarchy Report',
    'sequence': 51,
    'description': """
    Extrae de los codigos de cuenta los distintos niveles usados en los 
    informes contables (1,2,3).
    Mediante etiquetas para los distintos niveles crea un informe utilizando
    la funcionalidad BI para explotar la informacion contable jerarquizada.
    """,
    'category': 'Accounting',
    'author': 'Joaquin Gutierrez Pedrosa'
              'Odoo Community Association (OCA)',
    'website': 'https://www.gutierrezweb.es',
    'images': [
    ],
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/account.xml',
        'views/account_views.xml',
        'reports/bi_reporting_account_hierarchy.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
