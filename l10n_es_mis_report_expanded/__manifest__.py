# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
#                <contact@eficent.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

{
    'name': 'Plantillas MIS Builder para informes contables españoles, '
            'expandidas',
    'author': 'Eficent,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-spain',
    'category': 'Reporting',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'l10n_es_mis_report',
    ],
    'data': [
        'data/mis_report_balance_abreviated_expanded.xml',
        'data/mis_report_balance_normal_expanded.xml',
        'data/mis_report_balance_sme_expanded.xml',
        'data/mis_report_pyg_abreviated_expanded.xml',
        'data/mis_report_pyg_normal_expanded.xml',
        'data/mis_report_pyg_sme_expanded.xml',
        'data/mis_report_revenues_expenses_normal_expanded.xml',
    ],
    'installable': True,
}
