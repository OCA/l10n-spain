# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.tools import sql


def pre_init_hook(cr):
    if not sql.column_exists(cr, "purchase_order", "is_sigaus"):
        sql.create_column(cr, "purchase_order", "is_sigaus", "boolean")
    if not sql.column_exists(cr, "purchase_order", "sigaus_is_date"):
        sql.create_column(cr, "purchase_order", "sigaus_is_date", "boolean")
