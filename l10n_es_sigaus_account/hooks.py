# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


import logging

from odoo import tools
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)


def create_columns(cr):
    if not column_exists(cr, "account_move", "is_sigaus"):
        _logger.info("Initializing column is_sigaus on table account_move")
        tools.create_column(
            cr=cr,
            tablename="account_move",
            columnname="is_sigaus",
            columntype="boolean",
            comment="Indicates if it is a SIGAUS invoice",
        )

    if not column_exists(cr, "account_move", "sigaus_is_date"):
        _logger.info("Initializing column sigaus_is_date on table account_move")
        tools.create_column(
            cr=cr,
            tablename="account_move",
            columnname="sigaus_is_date",
            columntype="boolean",
            comment="Date indicator for SIGAUS",
        )

    if not column_exists(cr, "product_product", "sigaus_has_amount"):
        _logger.info("Initializing column sigaus_has_amount on table product_product")
        tools.create_column(
            cr=cr,
            tablename="product_product",
            columnname="sigaus_has_amount",
            columntype="boolean",
            comment="Indicates if the product has SIGAUS amount",
        )


def pre_init_hook(env):
    create_columns(env.cr)
