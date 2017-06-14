# -*- coding: utf-8 -*-
from openerp import models, api, fields, _


class L10nEsVatBookIssuedLines(models.Model):
    _name = 'l10n.es.vat.book.issued.lines'

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

    cuote = fields.Float(
        string=_('Cuote'))

    l10n_es_vat_book_id = fields.Many2one(
        comodel_name='l10n.es.vat.book',
        string=_('Vat Book id'))
