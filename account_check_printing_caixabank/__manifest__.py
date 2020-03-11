# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Check Printing Report Caixabank',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': "Creu Blanca,"
              "Odoo Community Association (OCA)",
    'category': 'Generic Modules/Accounting',
    'website': "https://github.com/OCA/l10n-spain",
    'depends': ['account_check_printing_report_base'],
    'data': [
        'data/report_paperformat.xml',
        'report/account_check_writing_report.xml',
        'views/report_check_caixabank.xml',
        'data/account_payment_check_report_data.xml',
    ],
    'installable': True,
}
