# -*- coding: utf-8 -*-
from openerp import models, api, fields, _


class L10nEsVatBookIssuedTaxSummary(models.Model):
    _name = 'l10n.es.vat.book.issued.tax.summary'

    tax_code_id = fields.Many2one(
        comodel_name='account.tax.code',
        string=_('Account Tax Code'),
        required=True,
        ondelete="cascade")

    sum_tax_amount = fields.Float(
        string=_('Summary tax amount'))

    sum_base_amount = fields.Float(
        string=_('Summary base amount'))

    tax_percent = fields.Float(
        string=_('Tax percent'))

    vat_book_id = fields.Many2one(
        comodel_name='l10n.es.vat.book',
        string=_('Libro de IVA'))
