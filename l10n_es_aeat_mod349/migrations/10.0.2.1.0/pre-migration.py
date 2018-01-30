# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    if not version:
        return
    from openupgradelib import openupgrade
    if not openupgrade.column_exists(cr, 'account_move_line',
                                     'aeat_349_operation_key'):
        return
    openupgrade.rename_columns(
        cr, {
            'account_move_line': [
                ('aeat_349_operation_key', None),
            ],
            'l10n_es_aeat_mod349_partner_record': [
                ('operation_key', None),
            ],
            'l10n_es_aeat_mod349_partner_refund': [
                ('operation_key', None),
            ],
        }
    )
