# Copyright 2019 Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountJournal(models.Model):
    _inherit = 'ir.sequence'

    def write(self, vals):
        """Don't change automatically prefix for journal entry sequences."""
        if (self.env.context.get('no_prefix_change') and len(vals) == 1
                and 'prefix' in vals):
            return True
        return super().write(vals)
