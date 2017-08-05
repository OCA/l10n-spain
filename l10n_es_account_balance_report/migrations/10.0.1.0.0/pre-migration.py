# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Remove trailing space in XML-ID"""
    openupgrade.rename_xmlids(
        env.cr, [
            ('l10n_es_account_balance_report.es_pyg_normal_49400 ',
             'l10n_es_account_balance_report.es_pyg_normal_49400',
             )
        ]
    )
