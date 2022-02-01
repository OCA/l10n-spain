# Copyright 2022 Moduon - Eduardo de Miguel
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import _, models

_logger = logging.getLogger(__name__)


class IrUIMenu(models.Model):
    _inherit = "ir.ui.menu"

    def _action_move_menus_to_account_accountant_menu_accounting(self):
        """Keep compatibility with account_accountant module"""
        self.ensure_one()
        try:
            account_accountant_top_level_menu = self.env.ref(
                "account_accountant.menu_accounting", raise_if_not_found=True
            )
            if not self.get_metadata().get("noupdate"):
                self.parent_id = account_accountant_top_level_menu
                _logger.info(
                    _(
                        "%s menu moved to %s"
                        % (self.name, account_accountant_top_level_menu.name)
                    )
                )
        except ValueError:
            pass
