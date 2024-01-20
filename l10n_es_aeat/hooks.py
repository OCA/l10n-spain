# Copyright 2022 Acsone SA - Xavier Bouquiaux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import tools
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)


def create_column_thirdparty_invoice(cr):
    if not column_exists(
        cr, "account_journal", "thirdparty_invoice"
    ) and not column_exists(cr, "account_move", "thirdparty_invoice"):
        _logger.info("Initializing column thirdparty_invoice on table account_move")
        tools.create_column(
            cr=cr,
            tablename="account_move",
            columnname="thirdparty_invoice",
            columntype="boolean",
            comment="Third-party invoice",
        )
        tools.create_column(
            cr=cr,
            tablename="account_journal",
            columnname="thirdparty_invoice",
            columntype="boolean",
            comment="Third-party invoice",
        )
        cr.execute("UPDATE account_move SET thirdparty_invoice = False")
        cr.execute("UPDATE account_journal SET thirdparty_invoice = False")


def pre_init_hook(env):
    create_column_thirdparty_invoice(env.cr)
