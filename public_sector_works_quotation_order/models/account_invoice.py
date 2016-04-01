# -*- coding: utf-8 -*-
################################################################
#    License, author and contributors information in:          #
#    __openerp__.py file at the root folder of this module.    #
################################################################

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('public_sector')
    def _compute_amount_material_exe(self):
        if self.public_sector:
            self.amount_material_exe = sum(
                line.price_subtotal for line in self.invoice_line)

    @api.one
    @api.depends('ge_percentage', 'amount_material_exe')
    def _compute_general_expenses(self):
        if self.public_sector:
            self.general_expenses = self.amount_material_exe * \
                self.ge_percentage / 100

    @api.one
    @api.depends('ip_percentage', 'amount_material_exe')
    def _compute_industrial_profit(self):
        if self.public_sector:
            self.industrial_profit = self.amount_material_exe * \
                self.ip_percentage / 100

    @api.one
    @api.depends('general_expenses', 'industrial_profit')
    def _compute_ge_ip_total(self):
        if self.public_sector:
            self.ge_ip_total = self.general_expenses + self.industrial_profit

    @api.one
    @api.depends('public_sector', 'ge_ip_total', 'invoice_line.price_subtotal',
                 'tax_line.amount', 'ot_percentage')
    def _compute_amount(self):
        if self.public_sector:
            self.amount_untaxed = self.amount_material_exe + self.ge_ip_total
            self.amount_tax = self.amount_untaxed * self.ot_percentage / 100
        else:
            self.amount_untaxed = sum(
                line.price_subtotal for line in self.invoice_line)
            self.amount_tax = sum(line.amount for line in self.tax_line)
        self.amount_total = self.amount_untaxed + self.amount_tax

    # compute_residual must be overwritten to take into account whether the
    # invoice is a public sector works one or not
    @api.one
    @api.depends(
        'state', 'currency_id', 'invoice_line.price_subtotal',
        'move_id.line_id.account_id.type',
        'move_id.line_id.amount_residual',
        # Fixes the fact that move_id.line_id.amount_residual, being not stored
        # and old API, doesn't trigger recomputation
        'move_id.line_id.reconcile_id',
        'move_id.line_id.amount_residual_currency',
        'move_id.line_id.currency_id',
        'move_id.line_id.reconcile_partial_id.line_partial_ids.invoice.type',
        'public_sector',
        # Must take into account general expenses and industrial profit if
        # public sector is True
    )
    # An invoice's residual amount is the sum of its unreconciled move lines
    # and, for partially reconciled move lines, their residual amount divided
    # by the number of times this reconciliation is used in an invoice (so we
    # split the residual amount between all invoice)
    def _compute_residual(self):
        self.residual = 0.0
        # Each partial reconciliation is considered only once for each invoice
        # it appears into, and its residual amount is divided by this number of
        # invoices
        partial_reconciliations_done = []
        for line in self.sudo().move_id.line_id:
            if line.account_id.type not in ('receivable', 'payable'):
                continue
            if line.reconcile_partial_id and line.reconcile_partial_id.id in \
               partial_reconciliations_done:
                continue
            # Get the correct line residual amount
            if line.currency_id == self.currency_id:
                line_amount = line.amount_residual_currency if \
                    line.currency_id else line.amount_residual
            else:
                from_currency = line.company_id.currency_id.with_context(
                    date=line.date)
                line_amount = from_currency.compute(
                    line.amount_residual, self.currency_id)
            # For partially reconciled lines, split the residual amount
            if line.reconcile_partial_id:
                partial_reconciliation_invoices = set()
                for pline in line.reconcile_partial_id.line_partial_ids:
                    if pline.invoice and self.type == pline.invoice.type:
                        partial_reconciliation_invoices.update(
                            [pline.invoice.id])
                line_amount = self.currency_id.round(line_amount / len(
                    partial_reconciliation_invoices))
                partial_reconciliations_done.append(
                    line.reconcile_partial_id.id)
            self.residual += line_amount
        self.residual = max(self.residual, 0.0)
        if self.public_sector:
            self.residual += (self.ge_ip_total)
            self.residual += (self.residual * self.ot_percentage / 100)

    public_sector = fields.Boolean(string='Public Sector Works', readonly=True,
                                   states={'draft': [('readonly', False)]})
    ot_percentage = fields.Integer(string='Order Tax Percentage', default=21,
                                   readonly=True,
                                   states={'draft': [('readonly', False)]})
    ge_percentage = fields.Integer(string='General Expenses Percentage',
                                   default=13, readonly=True,
                                   states={'draft': [('readonly', False)]})
    ip_percentage = fields.Integer(string='Industrial Profit Percentage',
                                   default=6, readonly=True,
                                   states={'draft': [('readonly', False)]})
    amount_material_exe = fields.Float(
        string='Amount Material Execution', digits=dp.get_precision('Account'),
        readonly=True, compute='_compute_amount_material_exe',
        help='Amount untaxed without general expenses neither industrial '
             'profit included.')
    general_expenses = fields.Float(
        string='General Expenses', digits=dp.get_precision('Account'),
        readonly=True, compute='_compute_general_expenses',
        help='General expenses.')
    industrial_profit = fields.Float(
        string='Industrial Profit', digits=dp.get_precision('Account'),
        readonly=True, compute='_compute_industrial_profit',
        help='Industrial profit.')
    ge_ip_total = fields.Float(
        string='GE and IP Sum', digits=dp.get_precision('Account'),
        readonly=True, compute='_compute_ge_ip_total',
        help='Sum of general expenses plus industrial profit.')
