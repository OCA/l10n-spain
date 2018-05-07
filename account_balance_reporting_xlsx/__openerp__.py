# -*- coding: utf-8 -*-
# Copyright 2014 Anubía, soluciones en la nube,SL (http://www.anubia.es)
# Copyright Juan Formoso <jfv@anubia.es>
# Copyright Alejandro Santana <alejandrosantana@anubia.es>
# Copyright Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# Copyright 2017 valentin vinagre <valentin.vinagre@qubiq.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Account balance reporting to XLSX",
    'summary': "Export Account balance reporting to XLSX",
    "version": "9.0.1.0.0",
    "category": "Accounting / Reports",
    "author": "Spanish Localization Team,Odoo Community Association (OCA)",
    'website': 'https://odoospain.odoo.com',
    "license": "AGPL-3",
    'depends': [
        'account_balance_reporting',
        'report_xlsx',
    ],
    'data': [
        'report/report.xml',
        'wizard/account_balance_reporting_wizard.xml',
    ],
    "application": False,
    "installable": True,
}
