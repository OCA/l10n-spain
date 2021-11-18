# Copyright (2021) Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    lroe_response_line_ids = fields.Many2many(
        comodel_name='lroe.operation.response.line',
        compute='_compute_lroe_response_line_ids',
        string='Responses')

    @api.depends(
        'tbai_invoice_ids',
        'tbai_invoice_ids.state',
        'tbai_cancellation_ids',
        'tbai_cancellation_ids.state')
    def _compute_lroe_response_line_ids(self):
        for record in self:
            response_line_model = self.env['lroe.operation.response.line']
            response_ids = record.tbai_invoice_ids.mapped('tbai_response_ids').ids
            response_ids += record.tbai_cancellation_ids.mapped('tbai_response_ids').ids
            response_lines = response_line_model.search(
                [('tbai_response_id', 'in', response_ids)]
            )
            record.lroe_response_line_ids = [(6, 0, response_lines.ids)]
