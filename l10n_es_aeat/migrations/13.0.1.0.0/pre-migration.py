from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.column_exists(env.cr, "account_move", "thirdparty_invoice"):
        openupgrade.add_fields(
            env,
            [
                (
                    "thirdparty_invoice",
                    "account.move",
                    "account_move",
                    "boolean",
                    False,
                    "l10n_es_aeat",
                ),
            ],
        )
