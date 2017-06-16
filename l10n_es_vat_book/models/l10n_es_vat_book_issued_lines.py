# -*- coding: utf-8 -*-
from openerp import models, api, fields, _


class L10nEsVatBookIssuedLines(models.Model):
    _name = 'l10n.es.vat.book.issued.lines'
    _order = 'invoice_id desc'

    invoice_date = fields.Date(
        string=_('Invoice Date'))

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string=_('Empresa'))

    vat_number = fields.Char(
        string=_('NIF'))

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string=_('Invoice'))

    base = fields.Float(
        string=_('Base'))

    tax_import = fields.Float(
        string=_('Tax import'))

    total = fields.Float(
        string=_('Total'))

    l10n_es_vat_book_id = fields.Many2one(
        comodel_name='l10n.es.vat.book',
        string=_('Vat Book id'))

    tax_line_issued_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.invoice.tax.lines',
        inverse_name='issued_invoice_line_id',
        string=_("Lineas de impuesto"))

    exeption = fields.Boolean(
        string=_("Exeption"))

    exeption_text = fields.Char(
        string=_("Exeption text"))
