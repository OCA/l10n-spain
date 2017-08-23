# -*- coding: utf-8 -*-
# Copyright 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2014-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    refund_invoices_description = fields.Text('Refund invoices description')
    origin_invoices_ids = fields.Many2many(
        comodel_name='account.invoice', column1='refund_invoice_id',
        column2='original_invoice_id', relation='account_invoice_refunds_rel',
        string='Refund invoice', help='Links to original invoice which is '
                                      'referred by current refund invoice',
    )
    refund_invoice_ids = fields.Many2many(
        comodel_name='account.invoice', column1='original_invoice_id',
        column2='refund_invoice_id', relation='account_invoice_refunds_rel',
        string="Refund invoices", readonly=True,
        help="Refund invoices created from this invoice")

    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None,
                        description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(
            invoice, date=date, period_id=period_id,
            description=description, journal_id=journal_id,
        )
        res['origin_invoices_ids'] = [(6, 0, invoice.ids)]
        res['refund_invoices_description'] = description
        refund_lines_vals = res['invoice_line']
        for i, line in enumerate(invoice.invoice_line):
            if i + 1 > len(refund_lines_vals):  # pragma: no cover
                # Avoid error if someone manipulate the original method
                break
            refund_lines_vals[i][2]['origin_line_ids'] = [(6, 0, line.ids)]
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    origin_line_ids = fields.Many2many(
        comodel_name='account.invoice.line', column1='refund_line_id',
        column2='original_line_id', string="Original invoice line",
        relation='account_invoice_line_refunds_rel',
        help="Original invoice line to which this refund invoice line "
             "is referred to")
    refund_line_ids = fields.Many2many(
        comodel_name='account.invoice.line', column1='original_line_id',
        column2='refund_line_id', string="Refund invoice line",
        relation='account_invoice_line_refunds_rel',
        help="Refund invoice lines created from this invoice line")
