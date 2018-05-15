# -*- coding: utf-8 -*-
# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    if not version:
        return

    list = {
        'mis_report_trial_balance_asoc_summary':
            'mis_report_trial_balance_asoc',
        'mis_report_trial_balance_full_summary':
            'mis_report_trial_balance_full',
        'mis_report_trial_balance_pymes_summary':
            'mis_report_trial_balance_pymes',
    }
    for key in list.keys():
        cr.execute("""
            UPDATE ir_model_data
            SET name = '%s'
            WHERE name = '%s'
            AND module = 'l10n_es_mis_report_trial_balance'
            """ % (list[key], key))
