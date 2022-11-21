# Copyright 2022 Moduon - Eduardo de Miguel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    thirdparty_invoice = fields.Boolean(
        string="Third-party invoice",
        copy=False,
    )
