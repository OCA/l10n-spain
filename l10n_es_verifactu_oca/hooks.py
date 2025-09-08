# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import tools


def pre_init_hook(env):
    """Avoid the heavy compute methods, specially when account.move table is very
    populated, pre-creating the columns and filling them with sane defaultes. Some of it
    is done on post-init hook.
    WARNING: For special cases like IGIC or other, the default value doesn't serve.
    """
    cr = env.cr
    column_exists = tools.sql.column_exists
    create_column = tools.sql.create_column
    if not column_exists(cr, "account_move", "verifactu_refund_type"):
        create_column(cr, "account_move", "verifactu_refund_type", "varchar")
        cr.execute(
            "UPDATE account_move SET verifactu_refund_type = 'I' "
            "WHERE move_type = 'out_refund'"
        )
    if not column_exists(cr, "account_move", "verifactu_registration_key"):
        create_column(cr, "account_move", "verifactu_registration_key", "int4")
        # Initialization done on post-init
    if not column_exists(cr, "account_move", "verifactu_tax_key"):
        create_column(cr, "account_move", "verifactu_tax_key", "varchar")
        cr.execute(
            "UPDATE account_move SET verifactu_tax_key = '01' "
            "WHERE move_type IN ('out_invoice', 'out_refund')"
        )


def post_init_hook(env):
    """Perform the initialization of this column once the registration keys have been
    loaded.
    WARNING: Only 01 case is covered here, so existing export/intra-community/other
    invoices should be changed later.
    """
    key = env.ref("l10n_es_verifactu_oca.verifactu_registration_keys_01")
    env.cr.execute(
        "UPDATE account_move SET verifactu_registration_key = %s "
        "WHERE move_type = 'out_refund' AND verifactu_registration_key IS NULL",
        (key.id,),
    )
