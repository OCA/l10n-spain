# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from psycopg2.extensions import AsIs


def migrate(cr, version):
    if not version:
        return
    from openupgradelib import openupgrade
    if not openupgrade.column_exists(
            cr, 'account_move_line',
            openupgrade.get_legacy_name('aeat_349_operation_key')
    ):
        return
    openupgrade.logged_query(
        cr, """
        UPDATE account_move_line
        SET l10n_es_aeat_operation_key = ml.operation_key
        FROM aeat_349_map_line ml
        WHERE ml.id = aml.%s
        """,
        (AsIs(openupgrade.get_legacy_name('aeat_349_operation_key')), ),
    )
    openupgrade.logged_query(
        cr, """
        UPDATE l10n_es_aeat_mod349_partner_record pr
        SET operation_key = ml.operation_key
        FROM aeat_349_map_line ml
        WHERE ml.id = pr.%s
        """,
        (AsIs(openupgrade.get_legacy_name('operation_key')), ),
    )
    openupgrade.logged_query(
        cr, """
        UPDATE l10n_es_aeat_mod349_partner_refund pr
        SET operation_key = ml.operation_key
        FROM aeat_349_map_line ml
        WHERE ml.id = pr.%s
        """,
        (AsIs(openupgrade.get_legacy_name('operation_key')), ),
    )
