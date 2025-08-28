# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

from odoo import Command


@openupgrade.migrate()
def migrate(env, version):
    for provider in env["payment.provider"].search([("code", "=", "redsys")]):
        if provider.redsys_pay_method == "z" and not provider.payment_method_ids:
            provider.payment_method_ids = [
                Command.set([env.ref("payment_redsys.payment_method_cc_bizum").id])
            ]
