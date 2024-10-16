# Copyright 2022 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

from .res_company import REPORTS_DEFINED, REPORTS_DEFINED_ONDELETE


class AccountJournal(models.Model):
    _inherit = "account.journal"

    account_check_printing_layout = fields.Selection(
        selection_add=REPORTS_DEFINED, ondelete=REPORTS_DEFINED_ONDELETE
    )
