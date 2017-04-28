# -*- coding: utf-8 -*-
# Copyright 2017 RGB Consulting S.L. (http://www.rgbconsulting.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "Informes financieros para España XLSX",
    'version': "8.0.1.0.0",
    'depends': [
        "l10n_es_account_financial_report",
        "report_xlsx"
    ],
    'license': "AGPL-3",
    'author': "RGB Consulting SL,"
              "Tecnativa"
              "Odoo Community Association (OCA)",
    'website': "https://odoo-community.org/",
    'category': "Localisation/Accounting",

    'data': [
        "wizard/wizard_print_journal_entries_view.xml",
        "report/l10n_es_reports.xml",
    ],
    "installable": True,
}
