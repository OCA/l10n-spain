# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.tools import sql


def pre_init_hook(env):
    if not sql.column_exists(env.cr, "sale_order", "is_sigaus"):
        sql.create_column(env.cr, "sale_order", "is_sigaus", "boolean")
    if not sql.column_exists(env.cr, "sale_order", "sigaus_is_date"):
        sql.create_column(env.cr, "sale_order", "sigaus_is_date", "boolean")
