# -*- coding: utf-8 -*-
# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountInvoiceLine(models.Model):
    """Inheritance of account invoce line to add some fields:
    - AEAT_349_operation_key: Operation key of invoice line
    """
    _inherit = 'account.invoice.line'

    aeat_349_operation_key = fields.Many2one(
        string='AEAT 349 Operation key',
        comodel_name='aeat.349.map.line',
    )

    @api.onchange('invoice_line_tax_ids')
    def _onchange_aeat_349_operation_key(self):
        if self.invoice_line_tax_ids:
            taxes = self.mapped('invoice_line_tax_ids').filtered(
                'aeat_349_operation_key')
            self.aeat_349_operation_key = taxes[0].aeat_349_operation_key

    @api.model
    def _get_invoice_lines_by_type(
            self, partner, operation_key, date_start=None, date_end=None):
        """
        Returns invoice lines ids by invoice type (supplier/customer) for dates
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
        invoice_line_domain = [
                  ('invoice_id', 'in', invoices.ids),
                  ('aeat_349_operation_key', '=', operation_key.id)]
        return self.search(invoice_line_domain)

    @api.multi
    def clean_refund_invoice_lines(
            self, partner, date_start, date_end):
        """Separate refunds from invoices"""
        invoice_lines = self.env['account.invoice.line']
        refund_lines = self.env['account.invoice.line']
        for inv_line in self:
            if inv_line.invoice_id.type in ('in_refund', 'out_refund'):
                if not inv_line.invoice_id.origin_invoice_ids:
                    invoice_lines += inv_line
                    continue
                origin_lines = inv_line.invoice_id.origin_invoice_ids.filtered(
                    lambda record: record.state in ('open', 'paid') and
                    record.partner_id.commercial_partner_id == partner)
                for origin_line in origin_lines:
                    if (origin_line.date <= date_start or
                            origin_line.date >= date_end):
                        refund_lines += inv_line
                    else:
                        invoice_lines += inv_line
            else:
                invoice_lines += inv_line
        return invoice_lines, refund_lines
