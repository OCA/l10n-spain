# -*- coding: utf-8 -*-
# Copyright 2017 Praxya (http://praxya.com/)
#                Daniel Rodriguez Lijo <drl.9319@gmail.com>
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
#                <contact@eficent.com>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import api, fields, models


class L10nEsVatBookLine(models.Model):
    _name = 'l10n.es.vat.book.line'
    _order = 'entry_number asc, ref asc, invoice_date asc'

    ref = fields.Char('Reference')
    entry_number = fields.Integer('Entry number')
    external_ref = fields.Char('External Reference')

    line_type = fields.Selection(selection=[
        ('issued', 'Issued'),
        ('received', 'Received'),
        ('rectification_issued', 'Refund Issued'),
        ('rectification_received', 'Refund Received')],
        string='Line type')
    invoice_date = fields.Date(
        string='Invoice Date')

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Empresa')

    vat_number = fields.Char(
        string='NIF')

    vat_book_id = fields.Many2one(
        comodel_name='l10n.es.vat.book',
        string='Vat Book id')

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')

    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry')
    tax_line_ids = fields.One2many(comodel_name='l10n.es.vat.book.line.tax',
                                   inverse_name='vat_book_line_id',
                                   string='Tax Lines', copy=False)

    exception = fields.Boolean(
        string="Exception")

    exception_text = fields.Char(
        string="Exception text")

    @api.multi
    @api.depends('tax_id')
    def _compute_tax_rate(self):
        for rec in self:
            rec.tax_rate = rec.tax_id.amount
