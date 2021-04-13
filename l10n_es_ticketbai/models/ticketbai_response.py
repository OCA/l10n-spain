# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields


class TicketBaiResponse(models.Model):
    _inherit = 'tbai.response'

    invoice_id = fields.Many2one(comodel_name='account.invoice')
