# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """UPDATE product_composition AS pc
        SET product_tmpl_id = pp.product_tmpl_id
        FROM product_product AS pp
        WHERE pc.product_id = pp.id
        AND pc.product_tmpl_id IS NULL""",
    )
