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
    'version': '10.0.2.0.0',
    'license': 'AGPL-3',
    'depends': [
        'l10n_es_mis_report',  # OCA/account-financial-reporting
    ],
    'data': [
        'data/mis_report_trial_balance_full_summary.xml',
        'data/mis_report_trial_balance_full_summary_subkpi.xml',
        'data/mis_report_trial_balance_pymes_summary.xml',
        'data/mis_report_trial_balance_pymes_summary_subkpi.xml',
        'data/mis_report_trial_balance_asoc_summary.xml',
        'data/mis_report_trial_balance_asoc_summary_subkpi.xml',
    ],
    'installable': True,
}
