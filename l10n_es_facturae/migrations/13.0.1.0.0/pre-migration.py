# Copyright 2020 Creu Blanca

from openupgradelib import openupgrade

models_to_rename = [
    ("account.invoice.integration", "account.move.integration"),
    ("account.invoice.integration.log", "account.move.integration.log"),
    ("account.invoice.integration.method", "account.move.integration.method"),
]

tables_to_rename = [
    ("account_invoice_integration", "account_move_integration"),
    ("account_invoice_integration_log", "account_move_integration_log"),
    ("account_invoice_integration_method", "account_move_integration_method"),
    (
        "account_invoice_integration_method_res_partner_rel",
        "account_move_integration_method_res_partner_rel",
    ),
]

column_renames = {
    "account_move_integration_method_res_partner_rel": [
        ("account_invoice_integration_method_id", "account_move_integration_method_id"),
    ],
}


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    openupgrade.rename_models(cr, models_to_rename)
    openupgrade.rename_tables(cr, tables_to_rename)
    openupgrade.rename_columns(env.cr, column_renames)

    # Add move_id to the `account.invoice.integration` model.
    openupgrade.logged_query(
        env.cr,
        """
            ALTER TABLE account_move_integration
            ADD COLUMN IF NOT EXISTS move_id INTEGER
        """,
    )
    # Link the move_id to the old account invoice's move.
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE account_move_integration aii
            SET move_id = am.id
            FROM account_move am
            WHERE am.old_invoice_id = aii.invoice_id
        """,
    )
    if openupgrade.column_exists(env.cr, "account_invoice", "integration_issue"):
        openupgrade.logged_query(
            env.cr,
            """
                ALTER TABLE account_move
                ADD COLUMN IF NOT EXISTS integration_issue BOOLEAN
            """,
        )
