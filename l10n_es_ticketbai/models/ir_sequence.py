#  Copyright 2021 Landoo Sistemas de Informacion SL
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    tbai_enabled = fields.Boolean(related="company_id.tbai_enabled", readonly=True)
