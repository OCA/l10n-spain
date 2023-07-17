# Copyright 2023 Alfredo de la Fuente - AvanzOSC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_rebu = fields.Boolean(
        string="Is Rebu", related="journal_id.is_rebu",
        store=True, copy=False
        )
