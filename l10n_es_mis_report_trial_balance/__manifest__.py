# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
#                <contact@eficent.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

{
    'name': 'Plantillas MIS Builder para Informe de Sumas y Saldos',
    'author': 'Eficent,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-spain',
    'category': 'Reporting',
    'version': '10.0.3.0.1',
    'license': 'AGPL-3',
    'depends': [
        'l10n_es_mis_report',  # OCA/account-financial-reporting
    ],
    'data': [
        'data/mis_report_trial_balance_full.xml',
        'data/mis_report_trial_balance_full_subkpi.xml',
        'data/mis_report_trial_balance_pymes.xml',
        'data/mis_report_trial_balance_pymes_subkpi.xml',
        'data/mis_report_trial_balance_asoc.xml',
        'data/mis_report_trial_balance_asoc_subkpi.xml',
    ],
    'installable': True,
}
