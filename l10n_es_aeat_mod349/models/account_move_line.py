# -*- coding: utf-8 -*-
# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountMoveLine(models.Model):
    """Inheritance of account move line to add some fields:
    - AEAT_349_operation_key: Operation key of invoice line
    """
    _inherit = 'account.move.line'

    aeat_349_operation_key = fields.Many2one(
        string='AEAT 349 Operation key',
        comodel_name='aeat.349.map.line',
        compute='_compute_aeat_349_operation_key',
        store=True,
    )

    @api.depends('tax_ids')
    def _compute_aeat_349_operation_key(self):
        for line in self:
            if line.tax_ids:
                taxes = line.mapped('tax_ids').filtered(
                    lambda x: x.aeat_349_operation_key)
                line.aeat_349_operation_key = taxes[0].aeat_349_operation_key

    @api.model
    def _get_move_lines_by_type(
            self, partner, operation_key, date_start=None, date_end=None):
        """
        Returns move lines ids by invoice type (supplier/customer) for dates
        """
        # Set type of invoice line
        invoice_type = ('in_invoice', 'out_invoice', 'in_refund', 'out_refund')
        invoice_domain = [
                  ('partner_id', 'child_of', partner.id),
                  ('state', 'in', ['open', 'paid']),
                  ('type', 'in', invoice_type),
                  ('date', '>=', date_start),
                  ('date', '<=', date_end)]
        invoices = self.env['account.invoice'].search(invoice_domain)
        move_line_domain = [
                  ('invoice_id', 'in', invoices.ids),
                  ('aeat_349_operation_key', '=', operation_key.id)]
        return self.search(move_line_domain)

    @api.multi
    def clean_refund_move_lines(
            self, partner, date_start, date_end):
        """Separate refunds from invoices"""
        move_lines = self.env['account.move.line']
        refund_lines = self.env['account.move.line']
        for move_line in self:
            if move_line.invoice_id.type in ('in_refund', 'out_refund'):
                if not move_line.invoice_id.origin_invoice_ids:
                    move_lines += move_line
                    continue
                origin_lines = (
                    move_line.invoice_id.origin_invoice_ids.filtered(
                        lambda record: record.state in ('open', 'paid') and
                        record.partner_id.commercial_partner_id == partner))
                for origin_line in origin_lines:
                    if (origin_line.date < date_start or
                            origin_line.date > date_end):
                        refund_lines += move_line
                    else:
                        move_lines += move_line
            else:
                move_lines += move_line
        return move_lines, refund_lines
