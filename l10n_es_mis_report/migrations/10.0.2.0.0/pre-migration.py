# -*- coding: utf-8 -*-
# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    if not version:
        return

    list = {
        'mis_report_es_balance_abreviado_summary':
            'mis_report_es_balance_abreviado',
        'mis_report_es_balance_normal_summary':
            'mis_report_es_balance_normal',
        'mis_report_es_balance_pymes_summary':
            'mis_report_es_balance_pymes',
        'mis_report_es_pyg_abreviado_summary':
            'mis_report_es_pyg_abreviado',
        'mis_report_es_pyg_normal_summary':
            'mis_report_es_pyg_normal',
        'mis_report_es_pyg_pymes_summary':
            'mis_report_es_pyg_pymes',
        'mis_report_es_eiyg_normal_summary':
            'mis_report_es_eiyg_normal',
    }
    for key in list.keys():
        cr.execute("""
            UPDATE ir_model_data
            SET name = '%s'
            WHERE name = '%s'
            AND module = 'l10n_es_mis_report'
            """ % (list[key], key))
