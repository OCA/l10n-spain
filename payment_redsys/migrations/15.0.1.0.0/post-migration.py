# Copyright 2023 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Set 'redsys_form' template to the field 'redirect_form_view_id'
    # in Redsys payment acquires
    env["payment.acquirer"].search([("provider", "=", "redsys")]).write(
        {"redirect_form_view_id": env.ref("payment_redsys.redsys_form").id}
    )
