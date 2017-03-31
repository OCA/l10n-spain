# -*- coding: utf-8 -*-
# Copyright 2009 Zikzakmedia S.L. - Jordi Esteve
# Copyright 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
# Copyright 2015 Tecnativa - Pedro M. Baeza
# Copyright 2017 RGB Consulting
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Informes financieros para España",
    'version': "8.0.1.0.0",
    'depends': [
        "account",
        "l10n_es"
    ],
    'license': "AGPL-3",
    'author': "Zikzakmedia SL,"
              "J. Gutierrez,"
              "Tecnativa,"
              "Odoo Community Association (OCA)",
    'website': "http://github.com/OCA/l10n-spain",
    'category': "Localisation/Accounting",

    'data': [
        "wizard/wizard_print_journal_entries_view.xml",
        "report/l10n_es_reports.xml",
        "views/templates.xml",
    ],
    "installable": True,
}
