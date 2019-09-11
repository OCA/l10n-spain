# Copyright 2019 Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    template_id = env.ref('payment_redsys.redsys_form').id
    sql = """
            UPDATE payment_acquirer
            SET view_template_id=%s
            WHERE provider = 'redsys'
        """
    openupgrade.logged_query(env.cr, sql, (template_id,))
