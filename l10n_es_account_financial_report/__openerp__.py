# -*- coding: utf-8 -*-
# Copyright 2009 Zikzakmedia S.L. (http://zikzakmedia.com)
#                Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
# Copyright 2015 Tecnativa S.L. (http://www.tecnativa.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Informes financieros para España",
    'version': "8.0.1.0.0",
    'author': "Spanish Localization Team,"
              "Zikzakmedia SL,"
              "J. Gutierrez,"
              "Tecnativa,"
              "Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/l10n-spain',
    'category': "Localisation/Accounting",
    'license': "AGPL-3",
    'depends': [
        "account",
        "l10n_es"
    ],
    'data': [
        "wizard/wizard_print_journal_entries_view.xml",
        "report/l10n_es_reports.xml",
    ],
    "installable": True,
}
