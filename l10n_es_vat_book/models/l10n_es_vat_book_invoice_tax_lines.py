# -*- coding: utf-8 -*-
from openerp import models, api, fields, _


class L10nEsVatBookInvoiceTaxLines(models.Model):
    _name = 'l10n.es.vat.book.invoice.tax.lines'

    name = fields.Char(
        string=_("Tax Name"))

    tax_percent = fields.Float(
        string=_("Tax percent"))

    tax_amount = fields.Float(
        string=_("Tax amount"))

    amount_without_tax = fields.Float(
        string=_("Base"))

    issued_invoice_line_id = fields.Many2one(
        comodel_name='l10n.es.vat.book.issued.lines',
        string=_("Issued invoice line"))

    received_invoice_line_id = fields.Many2one(
        comodel_name='l10n.es.vat.book.received.lines',
        string=_("Received invoice line"))
