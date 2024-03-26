# Copyright 2023 Bilbonet - Jesus Ramiro <bilbonet@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def update_lroe_operation_relation(env):
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO account_invoice_lroe_operation_rel
            (invoice_id, lroe_operation_id)
        SELECT am.id, ailor.lroe_operation_id
        FROM old_account_invoice_lroe_operation_rel as ailor
            INNER JOIN account_move am ON am.old_invoice_id = ailor.invoice_id
        """,
    )


def migration_invoice_moves(env):
    # Copy fields from invoices to linked moves
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET (lroe_state,
        tbai_vat_regime_purchase_key,
        tbai_vat_regime_purchase_key2,
        tbai_vat_regime_purchase_key3,
        lroe_invoice_dict
        ) = (
        ai.lroe_state,
        ai.tbai_vat_regime_purchase_key,
        ai.tbai_vat_regime_purchase_key2,
        ai.tbai_vat_regime_purchase_key3,
        ai.lroe_invoice_dict)
        FROM account_invoice ai
        WHERE ai.id = am.old_invoice_id""",
    )


@openupgrade.migrate()
def migrate(env, version):
    update_lroe_operation_relation(env)
    migration_invoice_moves(env)
