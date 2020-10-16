# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
#                <contact@eficent.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

{
    'name': 'Plantillas MIS Builder para informes contables españoles',
    'summary': """
        Plantillas MIS Builder para informes contables españoles""",
    'author': 'Eficent,'
              'Tecnativa,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-spain',
    'category': 'Reporting',
    'version': '11.0.2.1.0',
    'license': 'AGPL-3',
    'depends': [
        'mis_builder',  # OCA/mis-builder
    ],
    'data': [
        'data/mis_report_styles.xml',
        'data/mis_report_balance_abreviated.xml',
        'data/mis_report_balance_normal.xml',
        'data/mis_report_balance_sme.xml',
        'data/mis_report_pyg_abreviated.xml',
        'data/mis_report_pyg_normal.xml',
        'data/mis_report_pyg_sme.xml',
        'data/mis_report_revenues_expenses_normal.xml',
    ],
    'installable': True,
}
