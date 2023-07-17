# Copyright 2023 Alfredo de la Fuente - AvanzOSC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_rebu = fields.Boolean(
        string="Is Rebu", default=False, copy=False
        )
