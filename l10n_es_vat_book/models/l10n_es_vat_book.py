# -*- coding: utf-8 -*-
from openerp import models, api, fields, _


class L10nEsVatBook(models.Model):
    _inherit = "l10n.es.aeat.report"
    _name = 'l10n.es.vat.book'

    issued_invoice_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.issued.lines',
        inverse_name='l10n_es_vat_book_id',
        string=_('Issued invoices'))

    received_invoice_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.received.lines',
        inverse_name='l10n_es_vat_book_id',
        string=_('Received received'))

    rectification_invoice_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.rectification.lines',
        inverse_name='l10n_es_vat_book_id',
        string=_('Rectification received'))

    def __init__(self, pool, cr):
        self._aeat_number = 'vat_book'
        super(L10nEsVatBook, self).__init__(pool, cr)
