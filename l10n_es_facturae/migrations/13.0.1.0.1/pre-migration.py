# Copyright 2020 Creu Blanca

from openupgradelib import openupgrade

fields_to_unstore_safely = [
    "l10n_es_facturae.field_account_move_integration_log__type",
    "l10n_es_facturae.field_account_move_integration_log__state",
    "l10n_es_facturae.field_account_move_integration__state",
    # Just to be sure compatible without the previous version
    "l10n_es_facturae.field_account_invoice_integration_log__type",
    "l10n_es_facturae.field_account_invoice_integration_log__state",
    "l10n_es_facturae.field_account_invoice_integration__state",
]


@openupgrade.migrate()
def migrate(env, version):
    for field_key in fields_to_unstore_safely:
        field = env.ref(field_key, raise_if_not_found=False)
        if field:
            openupgrade.logged_query(
                env.cr, "UPDATE ir_model_fields SET store=false WHERE id=%s" % field.id
            )
    openupgrade.logged_query(
        env.cr,
        """
            DELETE FROM ir_model_relation imr
            USING ir_model im
            WHERE imr.model = im.id AND im.model IN (
                'account.move.integration',
                'account.move.integration.log',
                'account.move.integration.method'
            )""",
    )
    openupgrade.remove_tables_fks(
        env.cr,
        [
            "account_move_integration_method",
            "account_move_integration_log",
            "account_move_integration",
        ],
    )
