# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import tools
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)


def create_columns(cr):
    if not column_exists(cr, "sale_order", "is_sigaus"):
        _logger.info("Initializing column is_sigaus on table sale_order")
        tools.create_column(
            cr=cr,
            tablename="sale_order",
            columnname="is_sigaus",
            columntype="boolean",
        )

    if not column_exists(cr, "sale_order", "sigaus_is_date"):
        _logger.info("Initializing column sigaus_is_date on table sale_order")
        tools.create_column(
            cr=cr,
            tablename="sale_order",
            columnname="sigaus_is_date",
            columntype="boolean",
        )


def pre_init_hook(env):
    create_columns(env.cr)
