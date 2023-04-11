# Copyright 2023 Bilbonet - Jesus Ramiro <bilbonet@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade
from psycopg2 import sql


def update_tbai_invoice_relation(env):
    openupgrade.logged_query(
        env.cr,
        sql.SQL(
            """UPDATE tbai_invoice ti
            SET invoice_id = am.id
            FROM account_move am
            WHERE ti.{} = am.old_invoice_id"""
        ).format(sql.Identifier(openupgrade.get_legacy_name("invoice_id"))),
    )


def update_tbai_cancelled_invoice_relation(env):
    openupgrade.logged_query(
        env.cr,
        sql.SQL(
            """UPDATE tbai_invoice ti
            SET cancelled_invoice_id = am.id
            FROM account_move am
            WHERE ti.{} = am.old_invoice_id"""
        ).format(sql.Identifier(openupgrade.get_legacy_name("cancelled_invoice_id"))),
    )


def update_tbai_invoice_refund_origin_relation(env):
    openupgrade.logged_query(
        env.cr,
        sql.SQL(
            """UPDATE tbai_invoice_refund_origin tiro
            SET account_refund_invoice_id = am.id
            FROM account_move am
            WHERE tiro.{} = am.old_invoice_id"""
        ).format(
            sql.Identifier(openupgrade.get_legacy_name("account_refund_invoice_id"))
        ),
    )


def migration_invoice_moves(env):
    # Copy fields from invoices to linked moves
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET (tbai_invoice_id, tbai_cancellation_id,
        tbai_datetime_invoice, tbai_date_operation,
        tbai_description_operation, tbai_substitute_simplified_invoice,
        tbai_refund_key, tbai_refund_type,
        tbai_vat_regime_key, tbai_vat_regime_key2, tbai_vat_regime_key3
        ) = (
        ai.tbai_invoice_id, ai.tbai_cancellation_id,
        ai.tbai_datetime_invoice, ai.tbai_date_operation,
        ai.tbai_description_operation, ai.tbai_substitute_simplified_invoice,
        ai.tbai_refund_key, ai.tbai_refund_type,
        ai.tbai_vat_regime_key, ai.tbai_vat_regime_key2, ai.tbai_vat_regime_key3)
        FROM account_invoice ai
        WHERE ai.id = am.old_invoice_id""",
    )
    # We assign to the moves information from the matching invoices.
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET tbai_substitution_invoice_id = am.id
        FROM account_invoice ai
        WHERE ai.tbai_substitution_invoice_id = am.old_invoice_id
        AND ai.tbai_substitution_invoice_id IS NOT NULL""",
    )


@openupgrade.migrate()
def migrate(env, version):
    update_tbai_invoice_relation(env)
    update_tbai_cancelled_invoice_relation(env)
    update_tbai_invoice_refund_origin_relation(env)
    migration_invoice_moves(env)
