# -*- coding: utf-8 -*-
# © 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Importación de extractos bancarios españoles (Norma 43)',
    'category': 'Accounting & Finance',
    'version': '9.0.1.1.0',
    'license': 'AGPL-3',
    'author': 'Spanish Localization Team,'
              'Tecnativa,'
              'Odoo Community Association (OCA)',
    "website": "https://github.com/OCA/l10n-spain",
    'depends': [
        'account_bank_statement_import',
    ],
    'data': [
        'views/account_journal_views.xml',
        'wizards/account_bank_statement_import_view.xml',
    ],
    'installable': True,
}
