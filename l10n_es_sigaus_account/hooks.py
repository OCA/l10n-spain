# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.tools import sql


def pre_init_hook(cr):
    if not sql.column_exists(cr, "account_move", "is_sigaus"):
        sql.create_column(cr, "account_move", "is_sigaus", "boolean")
    if not sql.column_exists(cr, "account_move", "sigaus_is_date"):
        sql.create_column(cr, "account_move", "sigaus_is_date", "boolean")
    if not sql.column_exists(cr, "product_product", "sigaus_has_amount"):
        sql.create_column(cr, "product_product", "sigaus_has_amount", "boolean")
