# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Detect if the company doesn't have the taxes XML-IDs renamed (before the
    # taxpocalypse), and if so, rename them manually
    for comp in env["res.company"].search([]):
        for src, dest in [("s_iva0_e", "s_iva0_g_e"), ("s_iva0_ic", "s_iva0_g_i")]:
            if env.ref(
                f"account.{comp.id}_account_tax_template_{src}", False
            ) and not env.ref(f"account.{comp.id}_account_tax_template_{dest}", False):
                env["ir.model.data"].search(
                    [
                        ("module", "=", "account"),
                        ("name", "=", f"{comp.id}_account_tax_template_{src}"),
                    ]
                ).name = f"{comp.id}_account_tax_template_{dest}"
