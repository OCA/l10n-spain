# Copyright 2024 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class TicketBaiTax(models.Model):
    _inherit = "tbai.invoice.tax"

    not_subject_to_cause = fields.Selection(selection_add=[("IE", "IE")])
