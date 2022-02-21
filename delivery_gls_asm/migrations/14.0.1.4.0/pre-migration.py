# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "delivery_carrier", "gls_asm_is_return"):
        openupgrade.rename_fields(
            env,
            [
                (
                    "delivery.carrier",
                    "delivery_carrier",
                    "gls_asm_is_return",
                    "gls_asm_with_return",
                )
            ],
        )
